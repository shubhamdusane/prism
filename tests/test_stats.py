"""Stats + token-count tests."""

from __future__ import annotations

from prism.stats import token_count, estimate_savings, MODEL_PRICING


def test_token_count_nonempty():
    assert token_count("hello world") >= 1


def test_token_count_empty():
    assert token_count("") >= 0


def test_estimate_savings_returns_dataclass():
    text = "The authentication middleware handles tokens. " * 20
    s = estimate_savings(text, level="balanced")
    assert s.original_tokens > 0
    assert s.compressed_tokens >= 0
    assert 0.0 <= s.savings_pct <= 100.0


def test_estimate_savings_nonnegative():
    s = estimate_savings("short", level="safe")
    assert s.savings_tokens >= 0


def test_model_pricing_has_expected_keys():
    for k in ("gpt-4o", "claude-sonnet", "default"):
        assert k in MODEL_PRICING


def test_savings_str_format():
    s = estimate_savings("x " * 200, level="balanced")
    out = str(s)
    assert "prism balanced" in out
    assert "tokens" in out
    assert "saved" in out


def test_aggressive_saves_at_least_as_much_as_safe():
    text = "The system really is a very simple thing. " * 30
    safe = estimate_savings(text, level="safe")
    aggr = estimate_savings(text, level="aggressive")
    # Aggressive should save ≥ safe (may tie on short/trivial input).
    assert aggr.savings_pct >= safe.savings_pct - 1.0
