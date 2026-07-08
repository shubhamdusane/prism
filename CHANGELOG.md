# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-07-08

### Added
- Initial release of prism-llm
- Reversible semantic context compression for LLM agents
- `ContextCompressor` — lossless compression with anchor preservation
- Up to 80% token reduction while preserving critical information
- Anchor-based decompression for lossless reconstruction
- Span detection and classification (anchor, detail, filler)
- `prism compress` CLI command
- tiktoken integration for accurate token counting
- Comprehensive test suite
- `py.typed` marker for PEP 561
