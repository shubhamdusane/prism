"""CLI tests."""

from __future__ import annotations

import json
from pathlib import Path

from prism.cli import main


def test_cli_compress_and_expand_roundtrip(tmp_path: Path, capsys):
    src = tmp_path / "in.txt"
    compressed = tmp_path / "out.json"
    original = "Visit https://example.com. " + ("This is the same phrase. " * 10)
    src.write_text(original, encoding="utf-8")

    rc = main(["compress", str(src), "-o", str(compressed), "--level", "balanced"])
    assert rc == 0
    assert compressed.exists()

    payload = json.loads(compressed.read_text(encoding="utf-8"))
    assert "text" in payload and "anchors" in payload

    rc = main(["expand", str(compressed)])
    assert rc == 0
    captured = capsys.readouterr()
    # Expansion must contain the anchor URL verbatim.
    assert "https://example.com" in captured.out


def test_cli_stats(tmp_path: Path, capsys):
    src = tmp_path / "big.txt"
    src.write_text(("The system handles tokens. " * 100), encoding="utf-8")

    rc = main(["stats", str(src), "--level", "balanced"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "prism balanced" in out
    assert "tokens" in out


def test_cli_bench(tmp_path: Path, capsys):
    src = tmp_path / "big.txt"
    src.write_text(("The system handles tokens. " * 100), encoding="utf-8")

    rc = main(["bench", str(src)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "safe" in out
    assert "balanced" in out
    assert "aggressive" in out


def test_cli_install(capsys):
    rc = main(["install"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "prism" in out
    assert "hook" in out.lower() or "wrap_openai" in out
