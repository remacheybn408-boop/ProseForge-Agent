"""Local and Docker execution backend tests (Task 164)."""

from __future__ import annotations

from pathlib import Path

from proseforge_agent.cli import main
from proseforge_agent.environments import DockerBackendPlanner, LocalExecutionBackend


class FakeProcessRunner:
    def __init__(self) -> None:
        self.calls = []

    def run(self, command, *, cwd=None, env=None, timeout=None):
        self.calls.append({"command": command, "cwd": cwd, "env": env, "timeout": timeout})
        return {"stdout": "ok", "stderr": "", "exit_code": 0}


def test_local_backend_uses_safe_process_runner(tmp_path):
    runner = FakeProcessRunner()
    backend = LocalExecutionBackend(process_runner=runner, workspace_root=tmp_path)

    result = backend.run(["echo", "ok"], cwd=".", env={"TOKEN": "secret"}, timeout=5)

    assert result.stdout == "ok"
    assert result.exit_code == 0
    assert result.env["TOKEN"] == "[redacted]"
    assert runner.calls[0]["cwd"] == str(tmp_path)


def test_docker_backend_returns_dry_run_plan_without_docker(tmp_path):
    backend = DockerBackendPlanner(workspace_root=tmp_path, docker_available=False)

    plan = backend.check(image="python:3.11", dry_run=True, env_allowlist=["PATH"])

    assert plan.status == "unavailable"
    assert plan.dry_run is True
    assert plan.mounts[0]["host"] == str(Path(tmp_path).resolve())
    assert plan.env_allowlist == ["PATH"]
    assert "docker is not available" in plan.reason


def test_environment_cli_checks_local_and_docker(capsys):
    assert main(["environments", "check", "local", "--dry-run"]) == 0
    assert main(["environments", "check", "docker", "--dry-run"]) == 0

    out = capsys.readouterr().out
    assert "Local Environment" in out
    assert "Docker Environment" in out
