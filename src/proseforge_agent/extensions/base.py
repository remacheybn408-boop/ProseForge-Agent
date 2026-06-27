"""Extension contract and version compatibility.

Extensions let future providers, prompts, memory backends, retrievers, gates,
and other parts plug in without rewriting the core. Each extension declares an
id, a version, a compatible agent-version range, and the extension points
(capabilities) it implements. The registry enforces compatibility and isolates
failures; this module defines the contract those checks operate on.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..errors import ProseForgeAgentError

# The extension points the agent exposes.
EXTENSION_POINTS: tuple[str, ...] = (
    "provider",
    "memory_backend",
    "retriever",
    "workflow_step",
    "report_renderer",
    "gate",
    "prompt_pack",
    "market_analyzer",
    "export_target",
)


class ExtensionError(ProseForgeAgentError):
    """Raised when an extension is incompatible, malformed, or conflicting."""


_CLAUSE = re.compile(r"^(>=|<=|==|>|<)?\s*([0-9]+(?:\.[0-9]+)*)$")


def _parse_version(text: str) -> tuple[int, ...]:
    return tuple(int(part) for part in text.strip().split("."))


def _pad(a: tuple[int, ...], b: tuple[int, ...]) -> tuple[tuple[int, ...], tuple[int, ...]]:
    width = max(len(a), len(b))
    return a + (0,) * (width - len(a)), b + (0,) * (width - len(b))


def version_satisfies(version: str, spec: str) -> bool:
    """Return True if ``version`` satisfies a comma-separated range ``spec``.

    An empty spec, ``*``, or ``any`` matches anything. Each clause is an
    optional comparator (``>=``, ``<=``, ``==``, ``>``, ``<``; default ``>=``)
    followed by a dotted version.
    """
    spec = (spec or "").strip()
    if spec in ("", "*", "any"):
        return True
    current = _parse_version(version)
    for raw in spec.split(","):
        match = _CLAUSE.match(raw.strip())
        if not match:
            raise ExtensionError(f"invalid version range clause {raw!r}")
        op = match.group(1) or ">="
        target = _parse_version(match.group(2))
        left, right = _pad(current, target)
        if op == ">=" and not left >= right:
            return False
        if op == "<=" and not left <= right:
            return False
        if op == "==" and not left == right:
            return False
        if op == ">" and not left > right:
            return False
        if op == "<" and not left < right:
            return False
    return True


@dataclass
class Extension:
    """A versioned, capability-declaring plug-in point."""

    id: str
    version: str = "0.1.0"
    compatible_agent_range: str = "*"
    capabilities: tuple[str, ...] = ()
    enabled: bool = True

    def describe(self) -> dict:
        return {
            "id": self.id,
            "version": self.version,
            "compatible_agent_range": self.compatible_agent_range,
            "capabilities": list(self.capabilities),
            "enabled": self.enabled,
        }


@dataclass
class GateExtension(Extension):
    """A quality-gate extension that evaluates chapter text."""

    capabilities: tuple[str, ...] = ("gate",)

    def evaluate(self, text: str) -> dict:  # pragma: no cover - overridden
        raise NotImplementedError("gate extensions must implement evaluate()")


__all__ = [
    "EXTENSION_POINTS",
    "ExtensionError",
    "version_satisfies",
    "Extension",
    "GateExtension",
]
