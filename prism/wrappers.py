"""Drop-in proxies for OpenAI + Anthropic SDK clients.

Usage:
    from openai import OpenAI
    from prism import wrap_openai

    client = wrap_openai(OpenAI(), level="balanced")
    client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "<long context here>"}],
    )
    # prism compresses `content` before hitting the wire.

The wrapper is non-destructive: original SDK methods are preserved via
__getattr__. Only `.chat.completions.create` (OpenAI) and `.messages.create`
(Anthropic) are intercepted.
"""

from __future__ import annotations

from typing import Any

from .compressor import compress

_MIN_COMPRESS_CHARS = 500  # skip short prompts — compression overhead dominates


def _compress_messages(messages: list[dict[str, Any]], level: str) -> list[dict[str, Any]]:
    """Compress each message's `content` field if it is a long string."""
    out: list[dict[str, Any]] = []
    for msg in messages:
        content = msg.get("content")
        if isinstance(content, str) and len(content) >= _MIN_COMPRESS_CHARS:
            from typing import cast

            from .compressor import Level

            cc = compress(content, level=cast(Level, level))
            new_msg = dict(msg)
            new_msg["content"] = cc.to_prompt()
            out.append(new_msg)
        else:
            out.append(msg)
    return out


class _OpenAIChatCompletions:
    def __init__(self, inner: Any, level: str) -> None:
        self._inner = inner
        self._level = level

    def create(self, *args: Any, **kwargs: Any) -> Any:
        if "messages" in kwargs and isinstance(kwargs["messages"], list):
            kwargs["messages"] = _compress_messages(kwargs["messages"], self._level)
        return self._inner.create(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


class _OpenAIChat:
    def __init__(self, inner: Any, level: str) -> None:
        self._inner = inner
        self.completions = _OpenAIChatCompletions(inner.completions, level)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


class _OpenAIWrapper:
    def __init__(self, inner: Any, level: str) -> None:
        self._inner = inner
        self.chat = _OpenAIChat(inner.chat, level)
        self._prism_level = level

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


class _AnthropicMessages:
    def __init__(self, inner: Any, level: str) -> None:
        self._inner = inner
        self._level = level

    def create(self, *args: Any, **kwargs: Any) -> Any:
        if "messages" in kwargs and isinstance(kwargs["messages"], list):
            kwargs["messages"] = _compress_messages(kwargs["messages"], self._level)
        system = kwargs.get("system")
        if isinstance(system, str) and len(system) >= _MIN_COMPRESS_CHARS:
            from typing import cast

            from .compressor import Level

            cc = compress(system, level=cast(Level, self._level))
            kwargs["system"] = cc.to_prompt()
        return self._inner.create(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


class _AnthropicWrapper:
    def __init__(self, inner: Any, level: str) -> None:
        self._inner = inner
        self.messages = _AnthropicMessages(inner.messages, level)
        self._prism_level = level

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


# ─── Public API ──────────────────────────────────────────────────────────────


def wrap_openai(client: Any, level: str = "balanced") -> Any:
    """Wrap an OpenAI client so every .chat.completions.create call compresses messages."""
    return _OpenAIWrapper(client, level)


def wrap_anthropic(client: Any, level: str = "balanced") -> Any:
    """Wrap an Anthropic client so every .messages.create call compresses messages+system."""
    return _AnthropicWrapper(client, level)
