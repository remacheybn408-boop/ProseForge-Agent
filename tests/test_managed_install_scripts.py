"""Managed install scripts + planner tests (Task 187)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from proseforge_agent.cli import main
from proseforge_agent.install.installer_scripts import (
    InstallPhase,
    InstallPlan,
    ManagedInstallPlanner,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
_PHASES = ["preflight", "ensure_python", "ensure_manager", "install_package", "register_path", "post_verify"]


def test_plan_orders_phases_and_uses_uv_when_available():
    plan = ManagedInstallPlanner("linux", "x64", {"uv": True, "python311": True}).plan()

    assert isinstance(plan, InstallPlan)
    names = [p.name for p in plan.phases]
    assert names == _PHASES
    assert any("uv tool install proseforge-agent" in " ".join(p.command) for p in plan.phases)


def test_plan_falls_back_to_pipx_when_uv_missing():
    plan = ManagedInstallPlanner("linux", "x64", {"uv": False, "pipx": True, "python311": True}).plan()
    install = _phase(plan, "install_package")
    assert "pipx" in " ".join(install.command)
    assert "uv tool install" not in " ".join(install.command)


def test_plan_installs_uv_when_neither_manager_present():
    plan = ManagedInstallPlanner("linux", "x64", {"uv": False, "pipx": False, "python311": True}).plan()
    manager = _phase(plan, "ensure_manager")
    assert "astral.sh/uv" in " ".join(manager.command) or "uv" in " ".join(manager.command)
    assert manager.optional is False


def test_plan_refuses_to_install_inside_active_venv_without_flag():
    plan = ManagedInstallPlanner("linux", "x64", {"uv": True, "active_venv": True}).plan()
    assert plan.refused is True
    assert "venv" in plan.refusal_reason.lower()


def test_plan_allows_venv_with_flag():
    plan = ManagedInstallPlanner("linux", "x64", {"uv": True, "active_venv": True}).plan(allow_venv=True)
    assert plan.refused is False
    assert [p.name for p in plan.phases] == _PHASES


def test_plan_uses_git_ref_when_git_flag_supplied():
    plan = ManagedInstallPlanner("linux", "x64", {"uv": True}).plan(ref="v0.2.0")
    install = _phase(plan, "install_package")
    joined = " ".join(install.command)
    assert "git+" in joined
    assert "v0.2.0" in joined


def test_plan_registers_path_on_windows_via_setx():
    plan = ManagedInstallPlanner("windows", "amd64", {"uv": True, "python311": True}).plan()
    register = _phase(plan, "register_path")
    assert any("setx" in part.lower() for part in register.command) or "setx" in " ".join(register.command).lower()


def test_plan_registers_path_on_posix_via_local_bin():
    plan = ManagedInstallPlanner("linux", "x64", {"uv": True}).plan()
    register = _phase(plan, "register_path")
    assert ".local/bin" in " ".join(register.command)


def test_plan_is_pure_and_writes_no_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    ManagedInstallPlanner("linux", "x64", {"uv": True}).plan()
    assert list(tmp_path.iterdir()) == []


def test_shell_scripts_exist_and_are_sourced():
    assert (REPO_ROOT / "scripts" / "install.sh").exists()
    assert (REPO_ROOT / "scripts" / "install.ps1").exists()
    assert (REPO_ROOT / "scripts" / "_install_lib.sh").exists()
    install_sh = (REPO_ROOT / "scripts" / "install.sh").read_text(encoding="utf-8")
    assert "_install_lib.sh" in install_sh
    assert "set -eu" in install_sh or "set -euo pipefail" in install_sh


def test_cli_install_script_emits_sh_to_stdout(capsys):
    exit_code = main(["install", "script", "--emit", "sh"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "proseforge-agent" in out
    assert "uv" in out


def test_cli_install_script_emits_ps1_to_stdout(capsys):
    exit_code = main(["install", "script", "--emit", "ps1"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "proseforge-agent" in out


def test_shell_script_passes_shellcheck():
    shellcheck = shutil.which("shellcheck")
    if not shellcheck:
        pytest.skip("shellcheck not installed")
    result = subprocess.run(
        [shellcheck, str(REPO_ROOT / "scripts" / "install.sh")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def _phase(plan: InstallPlan, name: str) -> InstallPhase:
    for phase in plan.phases:
        if phase.name == name:
            return phase
    raise AssertionError(f"phase {name!r} not found in {[p.name for p in plan.phases]}")
