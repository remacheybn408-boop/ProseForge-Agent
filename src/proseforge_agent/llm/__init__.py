"""LLM provider gateway.

Workflows depend only on the normalized contract in :mod:`base` and resolve
providers through :class:`ProviderRegistry`. Concrete providers never import
workflow code (dependency direction is one-way).
"""

from .base import (
    STANDARD_ROLES,
    LLMProvider,
    Message,
    ProviderRequest,
    ProviderResult,
    ProviderSpec,
    StreamChunk,
    Usage,
)
from .fake import FakeProvider
from .registry import ProviderRegistry

__all__ = [
    "STANDARD_ROLES",
    "LLMProvider",
    "Message",
    "ProviderRequest",
    "ProviderResult",
    "ProviderSpec",
    "StreamChunk",
    "Usage",
    "FakeProvider",
    "ProviderRegistry",
]
