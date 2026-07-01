"""Execution environment abstraction tests (Task 163)."""

from __future__ import annotations

from proseforge_agent.cli import main
from proseforge_agent.environments import ExecutionCapabilities, FakeExecutionEnvironment


def test_fake_environment_returns_execution_result():
    env = FakeExecutionEnvironment(environment_id="fake-1")

    result = env.run(["echo", "hello"], cwd=".", env={"TOKEN": "secret"}, timeout=5)

    assert result.environment_id == "fake-1"
    assert result.exit_code == 0
    assert result.stdout == "echo hello"
    assert result.stderr == ""
    assert result.env["TOKEN"] == "[redacted]"
    assert result.capabilities.long_running_process is True


def test_fake_environment_timeout_and_output_truncation():
    env = FakeExecutionEnvironment(stdout_limit=6)

    timeout = env.run(["sleep"], timeout=0)
    truncated = env.run(["abcdefghi"])

    assert timeout.exit_code == 124
    assert timeout.timed_out is True
    assert truncated.stdout == "abcdef"
    assert truncated.stdout_truncated is True


def test_environment_capabilities_are_declared():
    capabilities = ExecutionCapabilities(filesystem_sync=True, network=False, gpu=False)

    assert capabilities.to_dict()["filesystem_sync"] is True
    assert capabilities.to_dict()["network"] is False


def test_environments_cli_lists_fake(capsys):
    assert main(["environments", "list", "--provider", "fake"]) == 0

    out = capsys.readouterr().out
    assert "Execution Environments" in out
    assert "fake" in out
