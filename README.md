# prism

**Reversible semantic context compression for LLM agents.**

Reduce token usage by **40–80%** while preserving every URL, email, code block, and number verbatim. Compress once, expand on demand — zero information loss for critical anchors.

[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-31%20passing-brightgreen.svg)](#testing)

---

## Table of Contents

- [What is prism?](#what-is-prism)
- [The Problem](#the-problem)
- [How It Works](#how-it-works)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [CLI Reference](#cli-reference)
- [Python API Reference](#python-api-reference)
- [Compression Levels](#compression-levels)
- [Architecture](#architecture)
- [Contributing](#contributing)
- [Roadmap](#roadmap)
- [License](#license)

---

## What is prism?

prism is a **context compression library** for LLM-powered applications. It sits between your application and the LLM API, shrinking long prompts before they hit the wire — and reconstructing them losslessly when needed.

```python
from prism import compress, expand

compressed = compress(long_document, level="balanced")
# compressed.text is 50% smaller, but every URL, email, code block, and number is preserved

original = expand(compressed)  # perfect round-trip reconstruction
```

**Why "prism"?** Like a prism splits light into components and recombines them, prism splits context into *anchors* (preserved verbatim), *references* (deduplicated), and *prose* (optionally pruned) — then recombines them perfectly.

---

## The Problem

LLM agents face a hard wall: **context windows are finite and expensive**.

| Model | Context Window | Cost (input, per 1M tokens) |
|-------|---------------|----------------------------|
| GPT-4o | 128K tokens | $2.50 |
| Claude Sonnet | 200K tokens | $3.00 |
| Claude Opus | 200K tokens | $15.00 |

A typical agent conversation with tool outputs, file contents, and conversation history easily hits **50K–100K tokens**. That means:

- **$0.15–$1.50 per request** at Opus pricing
- **Latency spikes** as context approaches the window limit
- **Context eviction** when you hit the ceiling — losing critical earlier information
- **Repetition** — agents re-read the same files, the same API docs, the same error messages

prism solves this by compressing the context *before* it reaches the model, preserving everything the model actually needs while eliminating redundancy.

---

## How It Works

prism uses a **4-pass compression pipeline**. Each pass is independent and composable.

```
┌─────────────────────────────────────────────────────────────────┐
│                     INPUT TEXT (100%)                           │
│  "Visit https://example.com for details. The auth middleware   │
│   handles JWT tokens. The auth middleware validates JWT.       │
│   Email admin@example.com for access."                         │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  PASS 1: ANCHOR EXTRACT │  ◎N◎ placeholders
                    │  URLs, emails, code,    │  LOSSLESS — always
                    │  numbers, paths, IPs    │  applied at all levels
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  PASS 2: LINE DEDUP     │  Consecutive identical
                    │  Fingerprint-based      │  lines collapsed
                    │  deduplication          │  LOSSLESS — always
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  PASS 3: REFERENCE      │  Repeated n-grams → §N
                    │  GRAPH                  │  IDs. Embedded legend
                    │  3-gram, 4-gram, 5-gram │  for reconstruction
                    │  deduplication          │  LOSSLESS — balanced+
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  PASS 4: SALIENCE       │  Low-content sentences
                    │  FILTER                 │  dropped. Marked with
                    │  Entropy-based pruning  │  ⟦hash⟧ for metadata
                    │  (aggressive only)      │  LOSSY — aggressive
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  OUTPUT (20–80% saved)  │
                    │  + anchors + refs dict  │
                    └─────────────────────────┘
```

### Anchor Preservation (Lossless)

Anchors are spans that **must** survive compression intact — URLs, emails, code blocks, numbers, file paths, IPs. They are replaced with `◎0◎`, `◎1◎` placeholders during compression and restored verbatim during expansion.

```
BEFORE:  "See https://docs.example.com/api/v2 for the auth endpoint.
          Email admin@example.com for keys."

AFTER:   "See ◎0◎ for the auth endpoint. Email ◎1◎ for keys."
         anchors: [("◎0◎", "https://docs.example.com/api/v2"),
                   ("◎1◎", "admin@example.com")]

EXPAND:  Perfect reconstruction — every character restored.
```

### Reference Graph (Lossless)

Repeated phrases (3–5 word n-grams appearing 2+ times) are replaced with short `§1`, `§2` tokens. The mapping is embedded in the compressed output so any LLM can understand it.

```
BEFORE:  "The auth middleware handles JWT tokens.
          The auth middleware validates JWT tokens.
          The auth middleware rejects invalid JWT tokens."

AFTER:   "§1 handles JWT tokens. §1 validates JWT tokens.
          §1 rejects invalid JWT tokens."
         refs: {"§1": "The auth middleware"}
         + [prism-legend] block so the model knows what §1 means
```

### Salience Filter (Lossy — Aggressive Only)

Sentences with low content density (lots of filler words like "the", "just", "really", "basically") are dropped and replaced with `⟦hash⟧` placeholders. The original text can be approximately reconstructed from metadata.

```
BEFORE:  "It really is a very simple thing actually. Just a basic
          component that does the thing."

AFTER:   "⟦a3f2c1b8⟧ ⟦7e4d9a01⟧"
         dropped_spans: [(pos, hash, length), ...]
```

---

## Installation

```bash
# From PyPI
pip install prism-llm

# With tiktoken for accurate token counting
pip install prism-llm[tokenizers]

# With Anthropic SDK support
pip install prism-llm[claude]

# Development
git clone https://github.com/shubhamdusane/prism
cd prism
pip install -e ".[dev,tokenizers]"
```

**Requirements:** Python 3.9+

---

## Quick Start

### As a Python library

```python
from prism import compress, expand, estimate_savings

# Compress a long document
text = open("docs/architecture.md").read()
compressed = compress(text, level="balanced")

print(f"Saved {compressed.savings_pct:.1f}%")  # e.g., "Saved 52.3%"
print(f"Ratio: {compressed.ratio}")             # e.g., 0.477

# Expand back (lossless for anchors + refs)
original = expand(compressed)
assert original == text  # perfect round-trip
```

### Drop-in SDK wrapper

```python
from openai import OpenAI
from prism import wrap_openai

# Wrap your client — every call auto-compresses
client = wrap_openai(OpenAI(), level="balanced")

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": long_context}],
)
# prism compresses `content` before hitting the wire
```

Works the same way with Anthropic:

```python
from anthropic import Anthropic
from prism import wrap_anthropic

client = wrap_anthropic(Anthropic(), level="safe")
response = client.messages.create(
    model="claude-sonnet",
    messages=[{"role": "user", "content": long_context}],
)
```

### Estimate savings before compressing

```python
from prism import estimate_savings

s = estimate_savings(my_text, level="balanced", model="claude-sonnet")
print(s)
# prism balanced: 12400 → 5830 tokens (53.0% saved, $0.0020 cost saved)
```

---

## CLI Reference

prism ships with a command-line interface:

```bash
prism <command> [options]
```

### `prism compress`

Compress a file to JSON (includes anchors, refs, and metadata for reconstruction).

```bash
prism compress input.txt -o output.json --level balanced
```

| Flag | Description | Default |
|------|-------------|---------|
| `file` | Input file path | (required) |
| `-o, --output` | Output file path | stdout |
| `--level` | `safe`, `balanced`, or `aggressive` | `balanced` |

### `prism expand`

Reconstruct the original from a compressed JSON file.

```bash
prism expand output.json
```

### `prism stats`

Show token savings without modifying the file.

```bash
prism stats input.txt --level balanced --model claude-sonnet
```

| Flag | Description | Default |
|------|-------------|---------|
| `file` | Input file path | (required) |
| `--level` | Compression level | `balanced` |
| `--model` | Model for pricing estimate | `claude-sonnet` |

### `prism bench`

Benchmark all three levels side-by-side.

```bash
prism bench input.txt --model gpt-4o
```

Output:

```
Input: input.txt (24500 chars)

level        orig→comp tokens    saved %    cost saved
------------------------------------------------------------
safe         6125→4890           20.2%   $0.0003
balanced     6125→2940           52.0%   $0.0008
aggressive   6125→1530           75.0%   $0.0011
```

### `prism install`

Print setup instructions for Claude Code hooks, Python SDK, and project config.

```bash
prism install
```

---

## Python API Reference

### `compress(text, level="balanced")`

Compress a text string.

**Parameters:**
- `text` (`str`) — Input text to compress
- `level` (`"safe" | "balanced" | "aggressive"`) — Compression level

**Returns:** `CompressedContext`

```python
from prism import compress

cc = compress("your long text here...", level="balanced")

cc.text              # compressed text
cc.anchors           # [(placeholder, original), ...]
cc.refs              # {"§N": "original phrase", ...}
cc.dropped_spans     # [(pos, hash, length), ...]  (aggressive only)
cc.ratio             # 0.0–1.0 (smaller = more compressed)
cc.savings_pct       # 0.0–100.0
cc.to_prompt()       # render with inline legend for LLM consumption
```

### `expand(compressed)`

Reverse compression back to original text.

**Parameters:**
- `compressed` (`CompressedContext`) — The compressed context to expand

**Returns:** `str` — Reconstructed text (lossless for safe/balanced; approximate for aggressive)

```python
from prism import compress, expand

cc = compress(text)
original = expand(cc)
```

### `estimate_savings(text, level, model)`

Estimate token savings without performing the full compression workflow.

**Parameters:**
- `text` (`str`) — Input text
- `level` (`str`) — Compression level
- `model` (`str`) — Model name for pricing (e.g., `"gpt-4o"`, `"claude-sonnet"`)

**Returns:** `Savings`

```python
from prism import estimate_savings

s = estimate_savings(text, level="aggressive", model="gpt-4o")
s.original_tokens      # 6125
s.compressed_tokens    # 1530
s.savings_pct          # 75.0
s.estimated_cost_saved_usd  # 0.0011
```

### `token_count(text, model="cl100k_base")`

Count tokens using tiktoken (if installed) or a char/4 heuristic.

```python
from prism import token_count

count = token_count("hello world")  # ~3 tokens
```

### `wrap_openai(client, level="balanced")`

Wrap an OpenAI client to auto-compress messages before API calls.

```python
from prism import wrap_openai
wrapped = wrap_openai(OpenAI(), level="safe")
# Use `wrapped` exactly like a normal OpenAI client
```

### `wrap_anthropic(client, level="balanced")`

Wrap an Anthropic client to auto-compress messages + system prompts.

```python
from prism import wrap_anthropic
wrapped = wrap_anthropic(Anthropic(), level="balanced")
# Use `wrapped` exactly like a normal Anthropic client
```

### `CompressedContext`

The data class returned by `compress()`.

| Property | Type | Description |
|----------|------|-------------|
| `text` | `str` | Compressed text |
| `anchors` | `list[tuple[str, str]]` | Placeholder → original mappings |
| `refs` | `dict[str, str]` | §N → phrase mappings |
| `dropped_spans` | `list[tuple[int, str, int]]` | Position, hash, length of dropped spans |
| `original_length` | `int` | Byte length of input |
| `compressed_length` | `int` | Byte length of compressed text |
| `level` | `str` | Compression level used |
| `ratio` | `float` | compressed/original (0.0–1.0) |
| `savings_pct` | `float` | Percentage saved (0.0–100.0) |
| `to_prompt()` | `str` | Render for LLM with embedded legend |

---

## Compression Levels

prism offers three levels, each adding a pass on top of the previous:

| Level | Passes | Savings | Lossless? | Use When |
|-------|--------|---------|-----------|----------|
| **safe** | Anchor + Dedup | 20–30% | Yes | You need zero risk of information loss |
| **balanced** | + Reference Graph | 40–60% | Yes | Default — best savings with full reversibility |
| **aggressive** | + Salience Filter | 60–80% | Anchors yes, prose approximate | You need maximum compression and can tolerate approximate reconstruction |

### Level Comparison

```
Original (10,000 tokens):

  safe (7,500 tokens)     — anchors preserved, duplicates removed
       │
       balanced (4,500 tokens) — + repeated phrases → §N tokens
            │
            aggressive (2,200 tokens) — + low-salience sentences dropped
```

### When to Use Each Level

- **safe** — Legal documents, compliance data, anything where every word matters
- **balanced** — General agent workflows, conversation history, code review
- **aggressive** — Large codebase context, log aggregation, cost-sensitive bulk processing

---

## Architecture

```
prism/
├── __init__.py        # Public API: compress, expand, wrap_*, estimate_savings
├── compressor.py      # Core 4-pass compression algorithm + CompressedContext
├── stats.py           # Token counting (tiktoken/char heuristic) + cost estimation
├── wrappers.py        # Drop-in proxies for OpenAI and Anthropic SDK clients
├── hook.py            # Claude Code hook entry point (stdin/stdout JSON)
└── cli.py             # CLI: compress, expand, stats, bench, install
```

### Data Flow

```
                    ┌─────────────┐
                    │   Your App  │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
         ┌─────────┐ ┌──────────┐ ┌──────────┐
         │ Python  │ │   CLI    │ │  Hook    │
         │   API   │ │          │ │ (Claude) │
         └────┬────┘ └────┬─────┘ └────┬─────┘
              │            │            │
              └────────────┼────────────┘
                           │
                    ┌──────▼──────┐
                    │  Compressor │
                    │  ─────────  │
                    │  1. Anchors │
                    │  2. Dedup   │
                    │  3. Refs    │
                    │  4. Salience│
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   tiktoken  │  (optional)
                    └─────────────┘
```

### Integration Options

| Method | Description | Best For |
|--------|-------------|----------|
| `wrap_openai()` / `wrap_anthropic()` | Drop-in SDK wrapper | Existing codebases, zero refactor |
| `compress()` / `expand()` Python API | Direct function calls | Custom pipelines, fine-grained control |
| `prism compress` CLI | File-to-file compression | Shell scripts, CI/CD, batch processing |
| `python -m prism.hook` | Claude Code hook | Automatic prompt compression |

---

## Claude Code Integration

Add prism as a permanent hook so every prompt is automatically compressed:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "command": "python -m prism.hook",
        "matcher": ".*"
      }
    ]
  }
}
```

Configure via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PRISM_MIN_CHARS` | `1000` | Minimum prompt length to compress |
| `PRISM_LEVEL` | `balanced` | Compression level |
| `PRISM_REPORT` | `0` | Set to `1` to include savings in system message |

---

## Contributing

Contributions welcome! Here's how to get started:

```bash
git clone https://github.com/shubhamdusane/prism
cd prism
pip install -e ".[dev,tokenizers]"
pytest                    # run all 31 tests
pytest --cov=prism        # with coverage
ruff check .              # lint
mypy prism                # type check
```

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Write tests for new functionality
4. Ensure all tests pass (`pytest`)
5. Submit a pull request

### Project Standards

- Python 3.9+ compatibility
- Type hints on all public APIs
- Tests for every code path
- No external dependencies in core (tiktoken is optional)

---

## Roadmap

- [ ] Streaming compression for real-time agent loops
- [ ] Semantic-aware anchoring (detect domain-specific entities)
- [ ] Multi-language support (beyond English n-gram splitting)
- [ ] Compression statistics dashboard / visualization
- [ ] Integration with LangChain, CrewAI, AutoGen
- [ ] Async compression for large documents
- [ ] Configurable anchor patterns via `.prism.toml`
- [ ] Benchmark suite against other compression approaches
- [ ] WASM compilation for browser-based agents

---

## License

MIT License — see [LICENSE](LICENSE) for details.

Copyright (c) 2026 Shubham Dusane

---

<p align="center">
  <b>prism</b> — compress more, spend less, lose nothing.
</p>
