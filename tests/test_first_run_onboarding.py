from pathlib import Path

import yaml

from proseforge_agent.cli import main
from proseforge_agent.install.first_run import FirstRunResult, FirstRunWizard


def test_first_run_writes_portable_config_without_absolute_machine_paths(tmp_path):
    result = FirstRunWizard(tmp_path / ".pf-agent").run(
        {"portable": True, "proseforge_root": "${PROSEFORGE_ROOT}"}
    )
    assert isinstance(result, FirstRunResult)
    assert result.mode == "portable"
    config = yaml.safe_load(result.config_path.read_text(encoding="utf-8"))
    assert config["proseforge_root"] == "${PROSEFORGE_ROOT}"
    assert "${PROSEFORGE_AGENT_WORKSPACE:-.pf-agent}" in result.config_path.read_text(encoding="utf-8")
    assert str(tmp_path) not in result.config_path.read_text(encoding="utf-8")


def test_rerun_on_existing_install_is_non_destructive(tmp_path):
    wizard = FirstRunWizard(tmp_path / ".pf-agent")
    first = wizard.run({"portable": True, "proseforge_root": "${PROSEFORGE_ROOT}"})
    first.config_path.write_text("sentinel: true\n", encoding="utf-8")
    second = wizard.run({"portable": True, "proseforge_root": "${PROSEFORGE_ROOT}"})
    assert second.status == "already_initialized"
    assert first.config_path.read_text(encoding="utf-8") == "sentinel: true\n"


def test_first_run_creates_full_workspace_tree(tmp_path):
    result = FirstRunWizard(tmp_path / ".pf-agent").run(
        {"portable": True, "proseforge_root": "${PROSEFORGE_ROOT}"}
    )
    for path in [
        result.config_path,
        result.workspace_path,
        result.provider_stub_path,
        result.doctor_report_path,
        result.workspace_path / "projects",
        result.workspace_path / "memory",
        result.workspace_path / "runs",
    ]:
        assert path.exists()


def test_first_run_supports_utf8_project_root_paths(tmp_path):
    result = FirstRunWizard(tmp_path / "代理").run(
        {"portable": True, "proseforge_root": "D:/小说/项目"}
    )
    assert "D:/小说/项目" in result.config_path.read_text(encoding="utf-8")


def test_first_run_cli_non_interactive(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    code = main(["init", "--portable", "--proseforge-root", "${PROSEFORGE_ROOT}", "--non-interactive"])
    out = capsys.readouterr().out
    assert code == 0
    assert "First Run" in out
    assert (tmp_path / ".pf-agent" / "config.yaml").exists()


def test_expected_config_fixture_is_portable():
    fixture = Path(__file__).parent / "fixtures" / "first-run-onboarding-wizard" / "expected_config.yaml"
    payload = yaml.safe_load(fixture.read_text(encoding="utf-8"))
    assert payload["workspace"] == "${PROSEFORGE_AGENT_WORKSPACE:-.pf-agent}/workspace"
