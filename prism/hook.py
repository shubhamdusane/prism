"""Claude Code hook entry point: `python -m prism.hook`.

Reads the hook event JSON from stdin, compresses any large prompt field
it finds, and emits the compressed form back as additionalContext so
the model receives fewer tokens.

Safe-by-default: if anything goes wrong, passes through silently.
"""

from __future__ import annotations

import json
import os
import sys

from .compressor import compress
from .stats import estimate_savings

MIN_CHARS = int(os.environ.get("PRISM_MIN_CHARS", "1000"))
LEVEL = os.environ.get("PRISM_LEVEL", "balanced")
REPORT = os.environ.get("PRISM_REPORT", "0") == "1"


def main() -> int:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return 0

        event = json.loads(raw)

        # Claude Code UserPromptSubmit hook shape (approximate):
        #   { "prompt": "...", "sessionId": "...", "timestamp": "..." }
        prompt = event.get("prompt", "")
        if not isinstance(prompt, str) or len(prompt) < MIN_CHARS:
            return 0  # passthrough

        from typing import cast

        from .compressor import Level

        cc = compress(prompt, level=cast(Level, LEVEL))
        compressed = cc.to_prompt()

        response: dict[str, object] = {
            "additionalContext": compressed,
            "continue": True,
        }

        if REPORT:
            s = estimate_savings(prompt, level=LEVEL)
            response["systemMessage"] = f"[prism] {s}"

        sys.stdout.write(json.dumps(response))
        return 0

    except Exception as e:  # noqa: BLE001 - a hook must never break the user's prompt
        # Never fail the user prompt. Log to stderr silently.
        sys.stderr.write(f"[prism-hook] error: {e}\n")
        return 0


if __name__ == "__main__":
    sys.exit(main())
