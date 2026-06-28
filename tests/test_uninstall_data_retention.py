import json
from pathlib import Path

import pytest

from proseforge_agent.cli import main
from proseforge_agent.errors import ConfigurationError
from proseforge_agent.install.app_dirs import AppDirs
from proseforge_agent.install.uninstall import UninstallPlanner


FIXTURE = Path(__file__).parent / "fixtures" / "uninstall-and-data-retention" / "installed_layout.json"


def _dirs():
    return AppDirs.for_platform(
        "linux",
        {"HOME": "/home/作者", "PROSEFORGE_AGENT_WORKSPACE": "/home/作者/.pf-agent"},
        portable=True,
    )


def test_remove_user_data_requires_confirmation_token():
    plan = UninstallPlanner(_dirs()).plan(remove_user_data=True)
    with pytest.raises(ConfigurationError):
        plan.execute(permission="system_write", confirmation_token=None)
    assert plan.execute(permission="system_write", confirmation_token="REMOVE_USER_DATA").status == "planned"


def test_binaries_and_shell_integration_can_be_removed_independently():
    plan = UninstallPlanner(_dirs()).plan()
    assert plan.actions["binaries"]
    assert plan.actions["shell_integration"]
    assert plan.actions["user_data"] == []


def test_cache_and_logs_removal_does_not_touch_user_data():
    plan = UninstallPlanner(_dirs()).plan()
    paths = " ".join(plan.actions["cache_logs"])
    assert ".pf-agent/data" not in paths


def test_planning_performs_no_deletion(tmp_path):
    target = tmp_path / "keep.txt"
    target.write_text("keep", encoding="utf-8")
    UninstallPlanner(_dirs()).plan()
    assert target.exists()


def test_chinese_project_paths_are_classified_as_user_data():
    plan = UninstallPlanner(_dirs()).plan(remove_user_data=True)
    assert any("作者" in note for note in plan.retained_paths + plan.actions["user_data"])


def test_uninstall_plan_cli(capsys):
    code = main(["uninstall", "--plan"])
    out = capsys.readouterr().out
    assert code == 0
    assert "Uninstall Plan" in out


def test_installed_layout_fixture_loads():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert "user_data" in payload
