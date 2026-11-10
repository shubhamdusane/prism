# prism

Experimental context compression for LLM prompts, in plain Python with no runtime dependencies.

prism holds URLs, emails, code, numbers, IPs and paths aside as "anchors", replaces repeated word
sequences with short `§N` tokens defined in an inline legend, drops consecutive duplicate lines,
and (at the most aggressive level) drops low-content sentences. It includes a `prism bench`
command so you can measure what it actually saves on **your** text.

> **Status: early, pre-1.0 (v0.1.0).** Savings are small or zero on ordinary documents and code
> (see [Measured results](#measured-results)). It only helps on text with a lot of repeated
> phrasing. Read [Status & limitations](#status--limitations) before using it.

## Install

Not published on PyPI. Install from GitHub:

```bash
pip install git+https://github.com/shubhamdusane/prism.git
# optional: exact token counts in `prism bench` / `estimate_savings` (OpenAI cl100k_base)
pip install "prism-llm[tokenizers] @ git+https://github.com/shubhamdusane/prism.git"
```

Or from a clone:

```bash
git clone https://github.com/shubhamdusane/prism.git
cd prism
pip install -e ".[dev,tokenizers]"
pytest
```

Declared as Python 3.9+; CI only tests 3.10, 3.11 and 3.12.

## Measured results

Reproduce with one command per file:

```bash
pip install -e ".[tokenizers]"
prism bench examples/sample_repetitive.txt
prism bench CODE_OF_CONDUCT.md
prism bench CONTRIBUTING.md
```

Token counts below use tiktoken `cl100k_base` (an OpenAI tokenizer, used here as a proxy; Claude
and other models tokenize differently). The compressed size includes the legend, and anchors are
written back verbatim, i.e. it is the size of the text you would actually send. Run on
2026-11-10 at v0.1.0.

| Input | safe | balanced | aggressive |
|---|---|---|---|
| `examples/sample_repetitive.txt` (synthetic: 6 sentences repeated 20x; best case) | 1200 -> 1200 (0.0%) | 1200 -> 774 (**35.5%**) | 1200 -> 774 (35.5%) |
| `CODE_OF_CONDUCT.md` (ordinary prose) | 1067 -> 1067 (0.0%) | 1067 -> 1160 (**+8.7% more tokens**) | 1067 -> 1160 (+8.7%) |
| `CONTRIBUTING.md` (ordinary prose + code blocks, at this commit) | 1793 -> 1793 (0.0%) | 1793 -> 1830 (+2.1% more tokens) | 1793 -> 1844 (+2.8%) |

Notes:

- `prism bench` shows "0.0%" when compression makes the text *longer*; the `orig->comp tokens`
  column shows the real counts.
- Without tiktoken installed, token counts fall back to `characters / 4`, which gives different
  numbers.
- Only one input shows a real reduction, and it is synthetic and intentionally repetitive. On real
  prose, code and tool output I tried (pytest output, `git log --stat`, the library's own source),
  savings were 0% at every level. Headline figures such as "40-80%" or "56-60%" that appeared in
  earlier drafts are **not supported** and have been removed.
- A small sample of the author's own files is not a benchmark. Measure on your own data.

## Quick start

```python
from prism import compress, expand, estimate_savings

text = open("examples/sample_repetitive.txt", encoding="utf-8").read()

cc = compress(text, level="balanced")  # "safe" | "balanced" | "aggressive"
prompt = cc.to_prompt()  # what you would send to a model (text + legend)
print(estimate_savings(text, level="balanced"))

restored = expand(cc)  # restores anchors and reference phrases
```

Client wrappers (compress long string `content` / `system` fields of a request, 500+ characters):

```python
from openai import OpenAI
from prism import wrap_openai, wrap_anthropic

client = wrap_openai(OpenAI(), level="balanced")
```

The model receives the compressed text plus the legend; it is not expanded on the way back.

### CLI

```bash
prism compress FILE [--level safe|balanced|aggressive] [-o OUT.json]   # JSON with text, anchors, refs
prism expand OUT.json                                                   # print restored text
prism stats FILE [--level ...] [--model claude-sonnet]                  # token estimate for one level
prism bench FILE [--model ...]                                          # all three levels
prism install                                                           # print setup notes
```

There is also an experimental Claude Code `UserPromptSubmit` hook (`python -m prism.hook`,
configured with `PRISM_MIN_CHARS`, `PRISM_LEVEL`, `PRISM_REPORT`). It was written against an
assumed hook payload shape and has not been verified against Claude Code; test before relying
on it.

## How it works

1. **Anchors**: regexes for URLs, emails, fenced and inline code, numbers (3+ characters), IPv4
   addresses and file paths are swapped for `◎N◎` placeholders so the later passes cannot alter them.
2. **Dedup**: consecutive duplicate lines are dropped (compared after stripping and lower-casing).
3. **Reference graph** (balanced, aggressive): repeated 3 to 5 word sequences become `§N` tokens
   (up to 99), defined in a `[prism-legend]` block appended to the prompt.
4. **Salience filter** (aggressive): sentences whose words are mostly filler words are replaced
   by a `⟦hash⟧` marker.

`to_prompt()` puts the anchors back in place, so a model sees URLs, code and numbers exactly as in
the original. The code is in `prism/compressor.py` (about 250 lines).

## Reversibility: what is and is not restored

`expand(compress(text, level))` returns the original text exactly for **safe** and **balanced**
when the input has no consecutive duplicate lines and does not itself contain prism's marker
strings (`◎N◎`, `§N`, `[prism-legend]`). This is checked by the tests in
`tests/test_compressor.py`, including a round trip over `CONTRIBUTING.md`.

Not restored:

- **Consecutive duplicate lines** are dropped for good by the dedup pass (all levels). For code,
  this includes legitimate repeated lines such as two closing braces in a row.
- **Aggressive** drops sentences; only a hash and length are kept (`dropped_spans`).
- Input that contains the marker strings above can round-trip incorrectly.

So the library is *partially* reversible, not lossless.

## Status & limitations

- **Early, v0.1.0, pre-1.0.** API may change. Single author, not reviewed by others.
- **Small gains on normal text.** See the measurements above: negative to zero on the ordinary
  documents and code I tested; the one clear win is a synthetic, highly repetitive input.
  Reference-graph tokens plus legend can cost more than they save on short or non-repetitive text.
- **English, whitespace-split words only.** The n-gram pass splits on spaces.
- **Token counts are estimates.** cl100k_base or `chars/4`; not the tokenizer of the model you call.
  Cost figures in `Savings` use a hard-coded price table that is only approximate and will go stale.
- **Models must follow the legend.** Whether a given model reads `§N` tokens correctly is not
  evaluated here; there is no accuracy or answer-quality evaluation.
- **Hook and wrappers are lightly tested** (unit tests with fake clients, no live API calls).
- Not implemented (earlier drafts listed some of these): streaming, async, LangChain/CrewAI
  integrations, `.prism.toml` configuration, semantic or entity-aware anchoring.

## Development

```bash
pip install -e ".[dev]"
pytest              # 38 tests
ruff check .
ruff format --check .
```

CI runs the same commands on Python 3.10, 3.11 and 3.12.

## License

MIT, see [LICENSE](LICENSE).
