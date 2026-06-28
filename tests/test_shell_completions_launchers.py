import json
from pathlib import Path

import pytest

from proseforge_agent.cli import main
from proseforge_agent.errors import ConfigurationError
from proseforge_agent.install.shell import CompletionScript, ShellCompletionRenderer, ShellInstaller


FIXTURE = Path(__file__).parent / "fixtures" / "shell-completions-and-launchers" / "expected_snippets.json"


def test_powershell_completion_contains_pf_agent_command():
    script = ShellCompletionRenderer().render("powershell")
    assert isinstance(script, CompletionScript)
    assert "pf-agent" in script.script_text
    assert script.install_action == "system_write"


def test_bash_zsh_fish_render_distinct_targets():
    renderer = ShellCompletionRenderer()
    targets = {renderer.render(shell).install_target for shell in ["bash", "zsh", "fish"]}
    assert len(targets) == 3


def test_uninstall_plan_removes_only_managed_snippet():
    plan = ShellInstaller().plan("bash", install=False)
    assert plan.action == "remove"
    assert "BEGIN PROSEFORGE AGENT" in plan.managed_marker
    assert plan.permission == "system_write"


def test_unknown_shell_raises_configuration_error():
    with pytest.raises(ConfigurationError):
        ShellCompletionRenderer().render("nu")


def test_install_target_uses_no_absolute_machine_path():
    script = ShellCompletionRenderer().render("powershell")
    assert not Path(script.install_target).is_absolute()


def test_completions_show_cli(capsys):
    code = main(["completions", "show", "--shell", "powershell"])
    out = capsys.readouterr().out
    assert code == 0
    assert "Shell Completion" in out
    assert "pf-agent" in out


def test_expected_snippets_fixture_loads():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert "powershell" in payload
