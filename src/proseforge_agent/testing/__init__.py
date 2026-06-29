"""Shared testing helpers for ProseForge Agent.

This package holds the single authoritative set of fakes used across contract
and golden tests, so cards stop defining drifting local doubles.
"""

from .fakes import (
    FakeHTTP,
    FakeKernel,
    FakeProvider,
    FakeRetrieval,
    FakeSessionStore,
    FakeTools,
)

__all__ = [
    "FakeProvider",
    "FakeTools",
    "FakeSessionStore",
    "FakeRetrieval",
    "FakeKernel",
    "FakeHTTP",
]
