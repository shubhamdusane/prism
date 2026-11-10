"""Wrapper tests using mock SDK clients."""

from __future__ import annotations

from typing import Any

from prism import wrap_anthropic, wrap_openai

# ─── Mock SDKs ────────────────────────────────────────────────────────────────


class _MockCompletions:
    def __init__(self) -> None:
        self.captured: dict[str, Any] = {}

    def create(self, **kwargs: Any) -> Any:
        self.captured = kwargs
        return {"ok": True}


class _MockChat:
    def __init__(self) -> None:
        self.completions = _MockCompletions()


class _MockOpenAI:
    def __init__(self) -> None:
        self.chat = _MockChat()
        self.api_key = "sk-test"


class _MockAnthropicMessages:
    def __init__(self) -> None:
        self.captured: dict[str, Any] = {}

    def create(self, **kwargs: Any) -> Any:
        self.captured = kwargs
        return {"ok": True}


class _MockAnthropic:
    def __init__(self) -> None:
        self.messages = _MockAnthropicMessages()
        self.api_key = "anthropic-test"


# ─── OpenAI wrapper ──────────────────────────────────────────────────────────


def test_openai_passthrough_for_short_messages():
    client = _MockOpenAI()
    wrapped = wrap_openai(client)
    wrapped.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "short"}],
    )
    assert client.chat.completions.captured["messages"][0]["content"] == "short"


def test_openai_compresses_long_messages():
    client = _MockOpenAI()
    wrapped = wrap_openai(client)
    long_content = "The authentication middleware handles tokens. " * 50
    wrapped.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": long_content}],
    )
    result = client.chat.completions.captured["messages"][0]["content"]
    assert len(result) < len(long_content)


def test_openai_exposes_unwrapped_attrs():
    client = _MockOpenAI()
    wrapped = wrap_openai(client)
    assert wrapped.api_key == "sk-test"


# ─── Anthropic wrapper ───────────────────────────────────────────────────────


def test_anthropic_passthrough_short():
    client = _MockAnthropic()
    wrapped = wrap_anthropic(client)
    wrapped.messages.create(
        model="claude-sonnet",
        messages=[{"role": "user", "content": "short"}],
    )
    assert client.messages.captured["messages"][0]["content"] == "short"


def test_anthropic_compresses_long_messages():
    client = _MockAnthropic()
    wrapped = wrap_anthropic(client)
    long_content = "The authentication middleware handles tokens. " * 50
    wrapped.messages.create(
        model="claude-sonnet",
        messages=[{"role": "user", "content": long_content}],
    )
    result = client.messages.captured["messages"][0]["content"]
    assert len(result) < len(long_content)


def test_anthropic_compresses_long_system_prompt():
    client = _MockAnthropic()
    wrapped = wrap_anthropic(client)
    long_system = "You are a helpful assistant that handles tokens. " * 50
    wrapped.messages.create(
        model="claude-sonnet",
        system=long_system,
        messages=[{"role": "user", "content": "hi"}],
    )
    assert len(client.messages.captured["system"]) < len(long_system)


def test_anthropic_short_system_passthrough():
    client = _MockAnthropic()
    wrapped = wrap_anthropic(client)
    wrapped.messages.create(
        model="claude-sonnet",
        system="you are helpful",
        messages=[{"role": "user", "content": "hi"}],
    )
    assert client.messages.captured["system"] == "you are helpful"
