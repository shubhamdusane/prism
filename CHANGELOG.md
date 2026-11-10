# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-07-08

### Added
- `compress` / `expand` with three levels (safe, balanced, aggressive)
- Anchor preservation (URLs, emails, code, numbers, IPs, paths), reference-graph substitution,
  consecutive-duplicate-line removal, salience filter (aggressive only)
- `prism compress|expand|stats|bench|install` CLI
- `wrap_openai` / `wrap_anthropic` client wrappers, Claude Code `UserPromptSubmit` hook
- Optional tiktoken token counting (falls back to a chars/4 estimate)
- `py.typed` marker for PEP 561

### Fixed (pre-release cleanup)
- `CompressedContext.to_prompt()` now writes anchors back verbatim. Previously it emitted
  placeholders (`◎N◎`) with no definitions, so a model never saw URLs/code blocks and the reported
  savings were overstated.
- `expand()` now restores nested anchors (e.g. a URL inside a code block).
- `prism bench` no longer crashes on Windows consoles with a legacy code page.

### Notes
- Earlier drafts claimed "up to 80%" and 56-60% reduction and "lossless" compression. These are not
  supported by measurement; see README "Measured results" and "Status & limitations".
