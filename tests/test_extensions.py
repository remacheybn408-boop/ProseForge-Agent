from pathlib import Path

import pytest

from proseforge_agent.extensions.base import Extension, ExtensionError, GateExtension
from proseforge_agent.extensions.registry import ExtensionRegistry

SAMPLE_PATH = (
    Path(__file__).parents[1] / "samples" / "extensions" / "sample_gate.py"
)


class _RaisingGate(GateExtension):
    def evaluate(self, text: str) -> dict:
        raise RuntimeError("boom")


def _ok_gate(gate_id: str = "ok_gate") -> GateExtension:
    class _Ok(GateExtension):
        def evaluate(self, text: str) -> dict:
            return {"gate": self.id, "passed": True, "detail": "ok"}

    return _Ok(id=gate_id, capabilities=("gate",), compatible_agent_range=">=0.1.0")


def test_extension_registry_rejects_incompatible_version():
    extension = Extension(id="sample", compatible_agent_range=">=9.0")
    with pytest.raises(ExtensionError, match="compatible"):
        ExtensionRegistry(agent_version="0.1.0").register(extension)


def test_compatible_extension_registers():
    reg = ExtensionRegistry(agent_version="0.1.0")
    reg.register(Extension(id="ok", compatible_agent_range=">=0.1.0"))
    assert "ok" in reg.list_ids()


def test_wildcard_range_is_compatible():
    reg = ExtensionRegistry(agent_version="0.1.0")
    reg.register(Extension(id="any1", compatible_agent_range="*"))
    reg.register(Extension(id="any2", compatible_agent_range=""))
    assert {"any1", "any2"} <= set(reg.list_ids())


def test_unknown_extension_point_rejected():
    reg = ExtensionRegistry(agent_version="0.1.0")
    with pytest.raises(ExtensionError, match="point"):
        reg.register(Extension(id="x", capabilities=("bogus",)))


def test_duplicate_extension_id_rejected():
    reg = ExtensionRegistry(agent_version="0.1.0")
    reg.register(Extension(id="dup"))
    with pytest.raises(ExtensionError, match="duplicate"):
        reg.register(Extension(id="dup"))


def test_failed_extension_is_isolated():
    reg = ExtensionRegistry(agent_version="0.1.0")
    bad = _RaisingGate(id="bad", capabilities=("gate",), compatible_agent_range=">=0.1.0")
    good = _ok_gate("good")
    reg.register(bad)
    reg.register(good)

    assert reg.safe_invoke(bad, "evaluate", "text") is None  # does not raise
    assert reg.get("bad").enabled is False
    assert reg.errors()
    # An unrelated extension still works.
    assert reg.safe_invoke(good, "evaluate", "text")["passed"] is True


def test_disabled_extension_skipped():
    reg = ExtensionRegistry(agent_version="0.1.0")
    good = _ok_gate("g1")
    reg.register(good)
    reg.disable("g1", reason="manual")
    assert good not in reg.enabled_extensions("gate")


def test_sample_gate_loads_and_validates():
    reg = ExtensionRegistry(agent_version="0.1.0")
    ext = reg.load_module(SAMPLE_PATH)
    reg.register(ext)
    assert ext.id in reg.list_ids()
    assert ext.evaluate("一段正文")["passed"] is True
    assert ext.evaluate("TODO 未完成")["passed"] is False
