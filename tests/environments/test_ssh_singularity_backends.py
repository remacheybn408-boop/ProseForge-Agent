"""SSH and Singularity backend tests (Task 165)."""

from __future__ import annotations

from proseforge_agent.cli import main
from proseforge_agent.environments import SSHBackendPlanner, SingularityBackendPlanner


def test_ssh_backend_redacts_connection_plan():
    backend = SSHBackendPlanner(ssh_available=False)

    plan = backend.check(profile="demo", host="writer@example.com", token="secret-token", dry_run=True)

    assert plan.status == "unavailable"
    assert plan.dry_run is True
    assert plan.profile == "demo"
    assert plan.connection["host"] == "[redacted]"
    assert plan.connection["token"] == "[redacted]"
    assert "ssh binary is not available" in plan.reason


def test_singularity_backend_reports_image_plan_without_runtime():
    backend = SingularityBackendPlanner(singularity_available=False)

    plan = backend.check(image="demo.sif", dry_run=True)

    assert plan.status == "unavailable"
    assert plan.image == "demo.sif"
    assert plan.command_prefix == ["singularity", "exec", "demo.sif"]
    assert "singularity binary is not available" in plan.reason


def test_ssh_singularity_cli_checks(capsys):
    assert main(["environments", "check", "ssh", "--profile", "demo", "--dry-run"]) == 0
    assert main(["environments", "check", "singularity", "--image", "demo.sif", "--dry-run"]) == 0

    out = capsys.readouterr().out
    assert "SSH Environment" in out
    assert "Singularity Environment" in out
