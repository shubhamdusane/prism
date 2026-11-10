"""prism — reversible semantic context compression for LLM agents.

Public API:
    compress(text, level="balanced") -> CompressedContext
    expand(compressed) -> str
    estimate_savings(text) -> Savings
    wrap_openai(client) -> wrapped client
    wrap_anthropic(client) -> wrapped client
"""

from .compressor import CompressedContext, compress, expand
from .stats import Savings, estimate_savings, token_count
from .wrappers import wrap_anthropic, wrap_openai

__version__ = "0.1.0"

__all__ = [
    "CompressedContext",
    "Savings",
    "compress",
    "estimate_savings",
    "expand",
    "token_count",
    "wrap_anthropic",
    "wrap_openai",
]
