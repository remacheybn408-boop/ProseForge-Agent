"""A worked example extension: a deterministic quality gate.

This is the reference an extension author copies. A gate extension subclasses
``GateExtension``, declares its id / version / compatible range / capabilities,
and implements ``evaluate(text) -> dict``. The module exposes a top-level
``EXTENSION`` instance so ``ExtensionRegistry.load_module`` can discover it.

Run it indirectly via the test suite (``tests/test_extensions.py``).
"""

from __future__ import annotations

from dataclasses import dataclass

from proseforge_agent.extensions.base import GateExtension


@dataclass
class SampleGate(GateExtension):
    """Fail a chapter draft that is empty or still contains a TODO marker."""

    def evaluate(self, text: str) -> dict:
        stripped = text.strip()
        if not stripped:
            return {"gate": self.id, "passed": False, "detail": "draft is empty"}
        if "TODO" in text:
            return {
                "gate": self.id,
                "passed": False,
                "detail": "draft still contains a TODO marker",
            }
        return {"gate": self.id, "passed": True, "detail": "no blocking issues"}


# Discovery entry point: the registry reads this attribute.
EXTENSION = SampleGate(
    id="sample_gate",
    version="0.1.0",
    compatible_agent_range=">=0.1.0",
    capabilities=("gate",),
)
