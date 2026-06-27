import shutil
import sys
from pathlib import Path

import pytest

from proseforge_agent.errors import EngineAdapterError
from proseforge_agent.proseforge import ProseForgeAdapter

FIXTURES = Path(__file__).parent / "fixtures" / "proseforge_engine"
SCRIPTS_REL = "plugin/proseforge-codex/scripts"


def _make_engine(root: Path, *, project=False, pipeline=False) -> Path:
    scripts = root / SCRIPTS_REL
    scripts.mkdir(parents=True, exist_ok=True)
    if project:
        shutil.copy(FIXTURES / "nf_project.py", scripts / "nf_project.py")
    if pipeline:
        shutil.copy(FIXTURES / "nf_pipeline.py", scripts / "nf_pipeline.py")
    return root


def test_discover_reports_missing_and_present_scripts(tmp_path):
    root = tmp_path / "engine"
    (root / "plugin/proseforge-codex/scripts").mkdir(parents=True)
    (root / "plugin/proseforge-codex/scripts/nf_project.py").write_text(
        "print('ok')", encoding="utf-8"
    )
    result = ProseForgeAdapter(root).discover()
    assert result.has_project_script is True
    assert result.has_pipeline_script is False


def test_discover_reports_both_scripts_present(tmp_path):
    root = _make_engine(tmp_path / "engine", project=True, pipeline=True)
    result = ProseForgeAdapter(root).discover()
    assert result.has_project_script is True
    assert result.has_pipeline_script is True
    assert result.is_usable is True


def test_dry_run_renders_command_without_executing(tmp_path):
    root = _make_engine(tmp_path / "engine", project=True)
    result = ProseForgeAdapter(root).run_project_action("inspect", dry_run=True)
    assert result.status == "dry_run"
    assert "--project-root" in result.command
    assert str(root) in result.command
    assert any("nf_project.py" in part for part in result.command)
    assert result.stdout == ""
    assert result.returncode is None


def test_run_executes_fake_script_and_parses_json_payload(tmp_path):
    root = _make_engine(tmp_path / "engine", project=True)
    result = ProseForgeAdapter(root).run_project_action("inspect", dry_run=False)
    assert result.status == "ok"
    assert result.returncode == 0
    assert result.payload is not None
    assert result.payload["status"] == "ok"
    assert result.payload["action"] == "inspect"
    assert result.stdout.strip() != ""


def test_run_keeps_raw_stdout_when_output_not_json(tmp_path):
    root = tmp_path / "engine"
    scripts = root / SCRIPTS_REL
    scripts.mkdir(parents=True)
    (scripts / "nf_project.py").write_text("print('plain text')", encoding="utf-8")
    result = ProseForgeAdapter(root).run_project_action("inspect", dry_run=False)
    assert result.payload is None
    assert "plain text" in result.stdout


def test_run_marks_error_on_nonzero_exit_without_raising(tmp_path):
    root = tmp_path / "engine"
    scripts = root / SCRIPTS_REL
    scripts.mkdir(parents=True)
    (scripts / "nf_project.py").write_text(
        "import sys; sys.exit(3)", encoding="utf-8"
    )
    result = ProseForgeAdapter(root).run_project_action("inspect", dry_run=False)
    assert result.status == "error"
    assert result.returncode == 3


def test_mutating_action_with_missing_script_raises(tmp_path):
    root = tmp_path / "engine"
    root.mkdir()
    with pytest.raises(EngineAdapterError):
        ProseForgeAdapter(root).run_project_action("create", dry_run=False)


def test_command_is_list_form_with_project_root(tmp_path):
    root = _make_engine(tmp_path / "engine", project=True)
    result = ProseForgeAdapter(root).run_project_action(
        "inspect", args=["--name", "Demo"], dry_run=True
    )
    assert isinstance(result.command, list)
    assert "--project-root" in result.command
    assert "--name" in result.command
    assert "Demo" in result.command


def test_timeout_raises_engine_adapter_error(tmp_path):
    root = tmp_path / "engine"
    scripts = root / SCRIPTS_REL
    scripts.mkdir(parents=True)
    (scripts / "nf_project.py").write_text(
        "import time; time.sleep(5)", encoding="utf-8"
    )
    adapter = ProseForgeAdapter(root, timeout_seconds=0.5)
    with pytest.raises(EngineAdapterError):
        adapter.run_project_action("inspect", dry_run=False)
