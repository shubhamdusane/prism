"""prism — reversible semantic context compression for LLM agents.

Public API:
    compress(text, level="balanced") -> CompressedContext
    expand(compressed) -> str
    estimate_savings(text) -> Savings
    wrap_openai(client) -> wrapped client
    wrap_anthropic(client) -> wrapped client
"""

from .compressor import compress, expand, CompressedContext
from .stats import estimate_savings, Savings, token_count
from .wrappers import wrap_openai, wrap_anthropic

__version__ = "0.1.0"

__all__ = [
    "compress",
    "expand",
    "CompressedContext",
    "estimate_savings",
    "Savings",
    "token_count",
    "wrap_openai",
    "wrap_anthropic",
]
