"""Compressor core tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from prism.compressor import compress, expand


def test_empty_string():
    cc = compress("")
    assert cc.text == ""
    assert cc.savings_pct == 0.0 or cc.ratio == 1.0


def test_short_string_roundtrip():
    original = "hello world"
    cc = compress(original, level="safe")
    assert expand(cc) == original


def test_anchor_preservation_url():
    original = "Visit https://example.com/path for details."
    cc = compress(original)
    assert "https://example.com/path" not in cc.text  # replaced with placeholder
    assert expand(cc) == original


def test_anchor_preservation_email():
    original = "Email alice@example.com for access."
    cc = compress(original)
    assert "alice@example.com" not in cc.text
    assert expand(cc) == original


def test_anchor_preservation_code_block():
    original = "See:\n```python\nprint('hello')\n```\nit works."
    cc = compress(original)
    assert "print('hello')" not in cc.text
    assert expand(cc) == original


def test_reference_graph_compresses_repetition():
    phrase = "the quick brown fox jumps over the lazy dog"
    repeated = (phrase + ". ") * 6
    cc = compress(repeated, level="balanced")
    # Should have built a ref for the repeated phrase.
    assert cc.refs, f"expected refs, got {cc.refs}"
    # Round-trip must match original.
    expanded = expand(cc)
    assert expanded.replace(" ", "") == repeated.replace(" ", "")


def test_dedup_consecutive_duplicate_lines():
    text = "line one\nline two\nline two\nline two\nline three"
    cc = compress(text, level="safe")
    # Consecutive duplicates collapsed.
    assert cc.text.count("line two") == 1


def test_savings_on_realistic_input():
    # Build a realistic agent context with repetition.
    context = "\n".join(
        [
            "User is asking about the authentication middleware.",
            "The authentication middleware handles JWT tokens.",
            "JWT tokens are validated by the authentication middleware.",
            "The authentication middleware rejects invalid JWT tokens.",
            "Error logs from the authentication middleware: line 42, line 43.",
            "Visit https://docs.example.com/auth for more on authentication middleware.",
        ]
        * 3
    )
    cc = compress(context, level="balanced")
    assert cc.savings_pct > 15.0, f"expected >15% savings, got {cc.savings_pct}"


def test_aggressive_level_drops_low_salience():
    text = (
        "The authentication system handles login. "
        "It really is a very simple thing actually. "
        "Just a basic component that does the thing. "
        "It uses JWT tokens for session management."
    )
    cc = compress(text, level="aggressive")
    # At least one span should be dropped for this input.
    assert len(cc.dropped_spans) >= 1


def test_type_error_on_non_string():
    with pytest.raises(TypeError):
        compress(123)  # type: ignore[arg-type]


def test_compressed_context_ratio_and_pct():
    cc = compress("a" * 100)
    assert 0.0 <= cc.ratio <= 1.0
    assert 0.0 <= cc.savings_pct <= 100.0


def test_to_prompt_includes_legend_when_refs():
    text = "the authentication middleware handles tokens. " * 5
    cc = compress(text, level="balanced")
    rendered = cc.to_prompt()
    if cc.refs:
        assert "[prism-legend]" in rendered
    else:
        assert rendered == cc.text


def test_level_safe_no_refs():
    text = "repeat this phrase. repeat this phrase. repeat this phrase."
    cc = compress(text, level="safe")
    assert cc.refs == {}


# ─── Regression + reversibility tests ───────────────────────────────────────

_MIXED = (
    "Deploy notes for build 20240115.\n"
    "Run `make release` then check https://ci.example.com/builds/4821 for status.\n"
    "```\n"
    "curl https://api.example.com/v1/items?limit=1000 -H 'x: y'\n"
    "```\n"
    "Contact ops@example.com or 10.0.0.12 if the path /var/log/app/error.log grows.\n"
)


def test_to_prompt_keeps_anchors_verbatim():
    # The text sent to a model must contain URLs/code/numbers exactly, not placeholders.
    cc = compress(_MIXED, level="safe")
    prompt = cc.to_prompt()
    assert "◎" not in prompt
    for needle in (
        "https://ci.example.com/builds/4821",
        "https://api.example.com/v1/items?limit=1000",
        "ops@example.com",
        "10.0.0.12",
        "/var/log/app/error.log",
        "`make release`",
    ):
        assert needle in prompt


@pytest.mark.parametrize("level", ["safe", "balanced"])
def test_roundtrip_exact_with_nested_anchors(level):
    # A URL inside a code block creates nested anchors; expand() must restore both.
    assert expand(compress(_MIXED, level=level)) == _MIXED


@pytest.mark.parametrize("level", ["safe", "balanced"])
def test_roundtrip_exact_on_repo_document(level):
    text = (Path(__file__).parent.parent / "CONTRIBUTING.md").read_text(encoding="utf-8")
    assert expand(compress(text, level=level)) == text


def test_consecutive_duplicate_lines_are_not_restored():
    # Documented limitation: the dedup pass drops consecutive duplicate lines for good.
    text = "alpha\n    }\n    }\nomega\n"
    assert expand(compress(text, level="safe")) != text


def test_aggressive_is_lossy():
    text = (
        "The authentication system handles login. "
        "It really is a very simple thing actually. "
        "Just a basic component that does the thing. "
        "It uses JWT tokens for session management."
    )
    cc = compress(text, level="aggressive")
    assert cc.dropped_spans
    assert expand(cc) != text
