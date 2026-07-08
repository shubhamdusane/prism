"""Token-count + savings estimation.

Uses tiktoken if available (accurate for OpenAI + most Claude models),
otherwise falls back to a char/4 heuristic (~4 chars/token for English).
"""

from __future__ import annotations

from dataclasses import dataclass

from .compressor import CompressedContext, compress


def token_count(text: str, model: str = "cl100k_base") -> int:
    """Count tokens in `text`. Exact with tiktoken, approximate otherwise."""
    try:
        import tiktoken

        try:
            enc = tiktoken.encoding_for_model(model)
        except KeyError:
            enc = tiktoken.get_encoding(model if "_" in model else "cl100k_base")
        return len(enc.encode(text))
    except ImportError:
        # Heuristic: English averages ~4 chars/token.
        return max(1, len(text) // 4)


@dataclass
class Savings:
    original_tokens: int
    compressed_tokens: int
    savings_tokens: int
    savings_pct: float
    original_chars: int
    compressed_chars: int
    level: str
    estimated_cost_saved_usd: float = 0.0

    def __str__(self) -> str:
        return (
            f"prism {self.level}: "
            f"{self.original_tokens} → {self.compressed_tokens} tokens "
            f"({self.savings_pct:.1f}% saved, "
            f"${self.estimated_cost_saved_usd:.4f} cost saved)"
        )


# Pricing (approximate, as of 2026-04). USD per 1M input tokens.
MODEL_PRICING: dict[str, float] = {
    "gpt-4o": 2.50,
    "gpt-4o-mini": 0.15,
    "claude-opus": 15.00,
    "claude-sonnet": 3.00,
    "claude-haiku": 0.25,
    "gemini-2.5-pro": 1.25,
    "default": 3.00,
}


def estimate_savings(
    text: str,
    level: str = "balanced",
    model: str = "claude-sonnet",
    include_legend: bool = True,
) -> Savings:
    """Return Savings dataclass comparing original vs compressed token count.

    Args:
        text: input string.
        level: compression level.
        model: pricing model for cost estimate.
        include_legend: if True, measure the compressed size including the
            legend payload sent to the LLM (more honest number).
    """
    from typing import cast

    from .compressor import Level

    cc: CompressedContext = compress(text, level=cast(Level, level))
    compressed_rendered = cc.to_prompt() if include_legend else cc.text

    orig_t = token_count(text)
    comp_t = token_count(compressed_rendered)
    saved = max(0, orig_t - comp_t)
    pct = (saved / orig_t * 100.0) if orig_t else 0.0
    price = MODEL_PRICING.get(model, MODEL_PRICING["default"])
    cost_saved = (saved / 1_000_000) * price

    return Savings(
        original_tokens=orig_t,
        compressed_tokens=comp_t,
        savings_tokens=saved,
        savings_pct=pct,
        original_chars=len(text),
        compressed_chars=len(compressed_rendered),
        level=level,
        estimated_cost_saved_usd=cost_saved,
    )
