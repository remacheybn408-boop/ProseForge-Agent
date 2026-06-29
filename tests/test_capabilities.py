"""Tests for capability flags and safe-mode boot (Task 66)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from proseforge_agent.capabilities import CapabilityRegistry
from proseforge_agent.errors import ConfigurationError

FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "capability-flags-and-safe-mode"
    / "capabilities.yaml"
)


def _boom(message: str = "boom"):
    def check():
        raise RuntimeError(message)

    return check


class _RecordingBus:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict]] = []

    def emit(self, event_type, payload=None, *, trace_id=None):
        self.events.append((event_type, payload or {}))


def test_failing_subsystem_self_check_is_auto_disabled_not_fatal():
    checks = {
        "chat": _boom(),
        "workflow": lambda: None,
    }
    cap_map = CapabilityRegistry(config={}, checks=checks).boot()  # must not raise
    assert cap_map.status("chat") == "disabled"
    assert cap_map.status("workflow") == "enabled"


def test_disabling_chat_leaves_writing_workflow_enabled():
    cap_map = CapabilityRegistry(
        config={"capabilities": {"chat": False}},
        checks={"workflow": lambda: None},
    ).boot()
    assert cap_map.status("chat") == "disabled"
    assert cap_map.status("workflow") == "enabled"


def test_calling_disabled_capability_returns_recovery_message_not_traceback():
    cap_map = CapabilityRegistry(config={"capabilities": {"chat": False}}).boot()
    with pytest.raises(ConfigurationError) as excinfo:
        cap_map.require("chat")
    message = str(excinfo.value)
    assert "Recovery" in message
    assert "trace" in message


def test_cli_flag_overrides_config_capability_value():
    # Config enables chat; the CLI flag disables it and wins.
    cap_map = CapabilityRegistry(
        config={"capabilities": {"chat": True}},
        cli_overrides={"chat": False},
    ).boot()
    assert cap_map.status("chat") == "disabled"
    assert "cli flag" in cap_map.reason("chat")


def test_safe_mode_emits_event_for_each_auto_disabled_capability():
    bus = _RecordingBus()
    checks = {"chat": _boom(), "memory": _boom()}
    CapabilityRegistry(config={}, checks=checks, event_bus=bus).boot()
    disabled = {payload["capability"] for _, payload in bus.events}
    assert disabled == {"chat", "memory"}
    assert all(event_type == "capability.auto_disabled" for event_type, _ in bus.events)


def test_core_capabilities_cannot_be_disabled():
    cap_map = CapabilityRegistry(
        config={"capabilities": {"config": False, "cli": False}},
        cli_overrides={"errors": False},
    ).boot()
    for core in ("config", "cli", "capabilities", "concurrency", "errors"):
        assert cap_map.status(core) == "enabled"


def test_disable_reason_supports_utf8_chinese_text():
    cap_map = CapabilityRegistry(
        config={}, checks={"retrieval": _boom("检索子系统启动失败：索引损坏")}
    ).boot()
    assert cap_map.status("retrieval") == "disabled"
    assert "检索子系统启动失败" in cap_map.reason("retrieval")


def test_config_flags_load_from_yaml_fixture():
    config = yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))
    cap_map = CapabilityRegistry(config=config).boot()
    assert cap_map.status("service") == "disabled"
    assert cap_map.status("chat") == "enabled"
