"""Modal and Daytona backend tests (Task 166)."""

from __future__ import annotations

from proseforge_agent.cli import main
from proseforge_agent.environments import DaytonaBackendPlanner, ModalBackendPlanner


def test_serverless_backend_reports_hibernation_plan():
    backend = ModalBackendPlanner(config={"token": "secret", "app": "demo"}, fake_state="hibernating")

    plan = backend.check(dry_run=True)

    assert plan.backend == "modal"
    assert plan.state == "hibernating"
    assert plan.status == "ok"
    assert plan.credentials["token"] == "[redacted]"
    assert "wake workspace" in plan.lifecycle_plan
    assert "hibernate workspace" in plan.lifecycle_plan


def test_serverless_backend_reports_missing_config_and_unavailable_provider():
    modal = ModalBackendPlanner(config={}, fake_state="missing_config")
    daytona = DaytonaBackendPlanner(config={"api_key": "secret"}, fake_state="unavailable")

    assert modal.check(dry_run=True).status == "missing_config"
    unavailable = daytona.check(dry_run=True)
    assert unavailable.backend == "daytona"
    assert unavailable.status == "unavailable"
    assert unavailable.credentials["api_key"] == "[redacted]"


def test_modal_daytona_cli_checks(capsys):
    assert main(["environments", "check", "modal", "--dry-run"]) == 0
    assert main(["environments", "check", "daytona", "--dry-run"]) == 0

    out = capsys.readouterr().out
    assert "Modal Environment" in out
    assert "Daytona Environment" in out
