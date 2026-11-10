"""prism CLI.

Commands:
    prism compress <file>          Compress a file; print to stdout (or -o).
    prism expand <file>            Expand a previously-compressed file.
    prism stats <file>             Print savings without modifying input.
    prism bench <file>             Run all 3 levels side-by-side.
    prism install                  Print Claude Code hook install instructions.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .compressor import CompressedContext, compress, expand
from .stats import estimate_savings


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def cmd_compress(args: argparse.Namespace) -> int:
    text = _read(args.file)
    cc = compress(text, level=args.level)
    payload = {
        "text": cc.text,
        "anchors": cc.anchors,
        "refs": cc.refs,
        "dropped_spans": cc.dropped_spans,
        "original_length": cc.original_length,
        "compressed_length": cc.compressed_length,
        "level": cc.level,
    }
    rendered = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
        print(f"wrote {args.output} ({cc.savings_pct:.1f}% saved)", file=sys.stderr)
    else:
        sys.stdout.write(rendered)
    return 0


def cmd_expand(args: argparse.Namespace) -> int:
    raw = _read(args.file)
    d = json.loads(raw)
    cc = CompressedContext(
        text=d["text"],
        anchors=[tuple(a) for a in d.get("anchors", [])],
        refs=d.get("refs", {}),
        dropped_spans=[tuple(s) for s in d.get("dropped_spans", [])],
        original_length=d.get("original_length", 0),
        compressed_length=d.get("compressed_length", 0),
        level=d.get("level", "balanced"),
    )
    sys.stdout.write(expand(cc))
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    text = _read(args.file)
    s = estimate_savings(text, level=args.level, model=args.model)
    print(s)
    return 0


def cmd_bench(args: argparse.Namespace) -> int:
    text = _read(args.file)
    print(f"\nInput: {args.file} ({len(text)} chars)\n")
    print(f"{'level':<12} {'orig→comp tokens':<22} {'saved %':<10} {'cost saved':<12}")
    print("-" * 60)
    for level in ("safe", "balanced", "aggressive"):
        s = estimate_savings(text, level=level, model=args.model)
        print(
            f"{level:<12} "
            f"{s.original_tokens}→{s.compressed_tokens:<15} "
            f"{s.savings_pct:>6.1f}%   "
            f"${s.estimated_cost_saved_usd:.4f}"
        )
    return 0


def cmd_install(args: argparse.Namespace) -> int:
    print(
        """
prism — one-line permanent install for Claude Code
===================================================

Option 1 — Python SDK user:
    pip install git+https://github.com/shubhamdusane/prism.git
    # Then in your code:
    from openai import OpenAI
    from prism import wrap_openai
    client = wrap_openai(OpenAI())     # every call now auto-compresses

Option 2 — Claude Code hook (permanent, no code change):
    Add to ~/.claude/settings.json:

    {
      "hooks": {
        "UserPromptSubmit": [
          {"command": "python -m prism.hook", "matcher": ".*"}
        ]
      }
    }

    Then: every prompt >500 chars is compressed before the model sees it.
    Expansion happens transparently on demand.

Option 3 — Per-project config (.prism.toml):
    [prism]
    level = "balanced"
    min_chars = 500
    enabled = true

Verify:
    prism stats my-big-context.txt
"""
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="prism", description="Reversible LLM context compression.")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("compress", help="Compress a file.")
    c.add_argument("file")
    c.add_argument("--level", choices=["safe", "balanced", "aggressive"], default="balanced")
    c.add_argument("-o", "--output")
    c.set_defaults(func=cmd_compress)

    e = sub.add_parser("expand", help="Expand a compressed JSON file.")
    e.add_argument("file")
    e.set_defaults(func=cmd_expand)

    s = sub.add_parser("stats", help="Show token savings without modifying.")
    s.add_argument("file")
    s.add_argument("--level", choices=["safe", "balanced", "aggressive"], default="balanced")
    s.add_argument("--model", default="claude-sonnet")
    s.set_defaults(func=cmd_stats)

    b = sub.add_parser("bench", help="Benchmark all 3 levels.")
    b.add_argument("file")
    b.add_argument("--model", default="claude-sonnet")
    b.set_defaults(func=cmd_bench)

    i = sub.add_parser("install", help="Show install / setup instructions.")
    i.set_defaults(func=cmd_install)

    return p


def main(argv: list[str] | None = None) -> int:
    # Windows consoles default to a legacy codec that cannot print the arrows/section
    # signs used in output; force UTF-8 so the CLI does not crash there.
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)  # type: ignore[no-any-return]


if __name__ == "__main__":
    sys.exit(main())
