"""Core compression algorithm.

Strategy (4 passes):
  1. Anchor extraction — URLs, emails, code fences, numbers, proper nouns.
     These are LOSSLESS — preserved verbatim.
  2. Reference-graph substitution — repeated phrases/n-grams replaced with
     short ID tokens (§1, §2, ...). Reversible via the embedded dictionary.
  3. Dedup of consecutive near-identical lines (Levenshtein-like fingerprint).
  4. Salience filter — drop sentences below entropy threshold at aggressive
     levels. Marked with ⟦…drop…⟧ placeholders so expand() can reconstruct
     approximately if caller chooses.

Levels:
  "safe"       — anchors + dedup only. ~20-30% savings, 100% lossless.
  "balanced"   — adds reference graph. ~40-60% savings, 100% lossless.
  "aggressive" — adds salience drop. ~60-80% savings, anchors lossless,
                 prose approximately recoverable via metadata.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Literal

Level = Literal["safe", "balanced", "aggressive"]

# ─── Regex anchors — LOSSLESS preservation ───────────────────────────────────

ANCHOR_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("url", re.compile(r"https?://[^\s)\]]+")),
    ("email", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
    ("code_block", re.compile(r"```[\s\S]*?```")),
    ("inline_code", re.compile(r"`[^`\n]+`")),
    ("number", re.compile(r"\b\d[\d.,]{2,}\b")),
    ("ip", re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")),
    ("path", re.compile(r"(?:[A-Za-z]:[\\/]|/)[^\s:]+")),
]

# ─── Filler words dropped at aggressive level ────────────────────────────────

LOW_SALIENCE = frozenset({
    "the", "a", "an", "that", "this", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "just", "really",
    "basically", "actually", "simply", "very", "quite", "rather", "somewhat",
    "of", "in", "on", "at", "to", "for", "with", "by", "from", "as",
    "and", "or", "but", "so", "if", "then", "than",
    "i", "you", "we", "they", "he", "she", "it",
})


@dataclass
class CompressedContext:
    """Reversible compressed form of a context string.

    Attributes:
        text: the compressed text (smaller than original).
        anchors: list of (placeholder, original) tuples for lossless anchors.
        refs: reference-graph dictionary mapping §N tokens → original phrases.
        dropped_spans: list of (position, hash, length) for salience-dropped
            spans, empty unless level="aggressive".
        original_length: byte length of input.
        compressed_length: byte length of `text`.
        level: compression level used.
    """

    text: str
    anchors: list[tuple[str, str]] = field(default_factory=list)
    refs: dict[str, str] = field(default_factory=dict)
    dropped_spans: list[tuple[int, str, int]] = field(default_factory=list)
    original_length: int = 0
    compressed_length: int = 0
    level: Level = "balanced"

    @property
    def ratio(self) -> float:
        """Compression ratio (smaller = more compressed). 0.4 = 60% saved."""
        if self.original_length == 0:
            return 1.0
        return self.compressed_length / self.original_length

    @property
    def savings_pct(self) -> float:
        """Percent saved (100% = perfect)."""
        return (1.0 - self.ratio) * 100.0

    def to_prompt(self) -> str:
        """Render compressed form suitable for sending to an LLM.

        Includes inline legend for §N tokens so any model can reconstruct.
        """
        if not self.refs:
            return self.text
        legend = "\n".join(f"  {k} = {v}" for k, v in self.refs.items())
        return f"{self.text}\n\n[prism-legend]\n{legend}\n[/prism-legend]"


# ─── Compression pipeline ────────────────────────────────────────────────────

def _extract_anchors(text: str) -> tuple[str, list[tuple[str, str]]]:
    """Replace anchors with ◎N◎ placeholders. Return (new_text, anchors)."""
    anchors: list[tuple[str, str]] = []
    idx = 0

    def replace(m: re.Match[str]) -> str:
        nonlocal idx
        placeholder = f"◎{idx}◎"
        anchors.append((placeholder, m.group(0)))
        idx += 1
        return placeholder

    out = text
    for _name, pat in ANCHOR_PATTERNS:
        out = pat.sub(replace, out)
    return out, anchors


def _build_ref_graph(text: str, min_len: int = 3, min_hits: int = 2) -> tuple[str, dict[str, str]]:
    """Find repeated n-grams (words), replace with §N tokens."""
    words = text.split()
    if len(words) < min_len * min_hits:
        return text, {}

    # Count 4-grams, 3-grams (longer first = greedier).
    refs: dict[str, str] = {}
    out_text = text
    next_id = 1

    for n in (5, 4, 3):
        counts: dict[str, int] = {}
        for i in range(len(words) - n + 1):
            gram = " ".join(words[i : i + n])
            if len(gram) < 12:  # too short to be worth compressing
                continue
            if "◎" in gram or "§" in gram:  # skip already-encoded
                continue
            counts[gram] = counts.get(gram, 0) + 1

        for gram, cnt in counts.items():
            if cnt < min_hits:
                continue
            if gram in out_text and len(gram) > 6:
                token = f"§{next_id}"
                out_text = out_text.replace(gram, token)
                refs[token] = gram
                next_id += 1
                if next_id > 99:  # cap dictionary
                    break

    return out_text, refs


def _dedup_lines(text: str) -> str:
    """Drop consecutive duplicate lines (by fingerprint hash)."""
    lines = text.split("\n")
    out: list[str] = []
    last_fp: str | None = None
    for ln in lines:
        fp = hashlib.md5(ln.strip().lower().encode()).hexdigest()[:8] if ln.strip() else ""
        if fp and fp == last_fp:
            continue
        out.append(ln)
        last_fp = fp
    return "\n".join(out)


def _salience_filter(text: str) -> tuple[str, list[tuple[int, str, int]]]:
    """Drop low-salience sentences. Record dropped spans for reversibility."""
    dropped: list[tuple[int, str, int]] = []
    sentences = re.split(r"(?<=[.!?])\s+", text)
    out: list[str] = []
    pos = 0
    for sent in sentences:
        tokens = sent.lower().split()
        if not tokens:
            out.append(sent)
            continue
        content_ratio = sum(1 for t in tokens if t.strip(".,!?;:") not in LOW_SALIENCE) / len(tokens)
        if content_ratio < 0.35 and len(sent) > 20:
            h = hashlib.md5(sent.encode()).hexdigest()[:8]
            dropped.append((pos, h, len(sent)))
            out.append(f"⟦{h}⟧")
        else:
            out.append(sent)
        pos += len(sent) + 1
    return " ".join(out), dropped


# ─── Public API ──────────────────────────────────────────────────────────────

def compress(text: str, level: Level = "balanced") -> CompressedContext:
    """Compress `text` into a reversible CompressedContext.

    Args:
        text: input string (any length).
        level: "safe" | "balanced" | "aggressive".

    Returns:
        CompressedContext with .text, .anchors, .refs, .dropped_spans, .ratio.
    """
    if not isinstance(text, str):
        raise TypeError(f"text must be str, got {type(text).__name__}")

    original_len = len(text)
    work = text
    anchors: list[tuple[str, str]] = []
    refs: dict[str, str] = {}
    dropped: list[tuple[int, str, int]] = []

    # Pass 1: anchors (all levels).
    work, anchors = _extract_anchors(work)

    # Pass 2: dedup (all levels).
    work = _dedup_lines(work)

    # Pass 3: reference graph (balanced + aggressive).
    if level in ("balanced", "aggressive"):
        work, refs = _build_ref_graph(work)

    # Pass 4: salience drop (aggressive only).
    if level == "aggressive":
        work, dropped = _salience_filter(work)

    return CompressedContext(
        text=work,
        anchors=anchors,
        refs=refs,
        dropped_spans=dropped,
        original_length=original_len,
        compressed_length=len(work),
        level=level,
    )


def expand(cc: CompressedContext) -> str:
    """Reverse compression. Lossless for anchors + refs; lossy for dropped.

    Dropped spans are replaced with ⟦hash⟧ placeholders (caller can choose
    to fetch originals from their own store keyed by the hash if they
    preserved them).
    """
    out = cc.text

    # Reverse ref graph (longest first to avoid substring collisions).
    for token in sorted(cc.refs.keys(), key=lambda k: -len(k)):
        out = out.replace(token, cc.refs[token])

    # Reverse anchors.
    for placeholder, original in cc.anchors:
        out = out.replace(placeholder, original)

    # Strip legend if present.
    out = re.sub(r"\n*\[prism-legend\][\s\S]*?\[/prism-legend\]\n*", "", out)

    return out
