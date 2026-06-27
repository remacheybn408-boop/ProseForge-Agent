import pytest

from proseforge_agent.config import load_agent_config
from proseforge_agent.errors import ConfigurationError


def _write_config(path, body):
    path.write_text(body, encoding="utf-8")
    return path


def test_load_agent_config_expands_environment_paths(tmp_path, monkeypatch):
    monkeypatch.setenv("PROSEFORGE_ROOT", str(tmp_path / "engine"))
    monkeypatch.delenv("PROSEFORGE_AGENT_WORKSPACE", raising=False)
    cfg_file = tmp_path / "agent.yaml"
    cfg_file.write_text(
        """paths:
  proseforge_root: ${PROSEFORGE_ROOT}
  workspace_root: ${PROSEFORGE_AGENT_WORKSPACE:-.pf-agent}
project:
  slug: demo
  title: Demo
""",
        encoding="utf-8",
    )
    cfg = load_agent_config(cfg_file)
    assert cfg.proseforge_root == tmp_path / "engine"
    assert cfg.workspace_root == tmp_path / ".pf-agent"


def test_default_used_when_env_var_unset(tmp_path, monkeypatch):
    monkeypatch.setenv("PROSEFORGE_ROOT", str(tmp_path / "engine"))
    monkeypatch.delenv("PROSEFORGE_AGENT_WORKSPACE", raising=False)
    cfg_file = _write_config(
        tmp_path / "agent.yaml",
        """paths:
  proseforge_root: ${PROSEFORGE_ROOT}
  workspace_root: ${PROSEFORGE_AGENT_WORKSPACE:-.pf-agent}
project:
  slug: demo
  title: Demo
""",
    )
    cfg = load_agent_config(cfg_file)
    assert cfg.workspace_root == tmp_path / ".pf-agent"


def test_explicit_env_overrides_default(tmp_path, monkeypatch):
    monkeypatch.setenv("PROSEFORGE_ROOT", str(tmp_path / "engine"))
    monkeypatch.setenv("PROSEFORGE_AGENT_WORKSPACE", str(tmp_path / "custom_ws"))
    cfg_file = _write_config(
        tmp_path / "agent.yaml",
        """paths:
  proseforge_root: ${PROSEFORGE_ROOT}
  workspace_root: ${PROSEFORGE_AGENT_WORKSPACE:-.pf-agent}
project:
  slug: demo
  title: Demo
""",
    )
    cfg = load_agent_config(cfg_file)
    assert cfg.workspace_root == tmp_path / "custom_ws"


def test_missing_project_slug_reports_key(tmp_path, monkeypatch):
    monkeypatch.setenv("PROSEFORGE_ROOT", str(tmp_path / "engine"))
    cfg_file = _write_config(
        tmp_path / "agent.yaml",
        """paths:
  proseforge_root: ${PROSEFORGE_ROOT}
  workspace_root: ${PROSEFORGE_AGENT_WORKSPACE:-.pf-agent}
project:
  title: Demo
""",
    )
    with pytest.raises(ConfigurationError) as exc:
        load_agent_config(cfg_file)
    assert "project.slug" in str(exc.value)


def test_unset_var_without_default_raises(tmp_path, monkeypatch):
    monkeypatch.setenv("PROSEFORGE_ROOT", str(tmp_path / "engine"))
    monkeypatch.delenv("UNSET_NO_DEFAULT", raising=False)
    cfg_file = _write_config(
        tmp_path / "agent.yaml",
        """paths:
  proseforge_root: ${PROSEFORGE_ROOT}
  workspace_root: ${UNSET_NO_DEFAULT}
project:
  slug: demo
  title: Demo
""",
    )
    with pytest.raises(ConfigurationError) as exc:
        load_agent_config(cfg_file)
    assert "UNSET_NO_DEFAULT" in str(exc.value)


def test_relative_workspace_resolves_from_config_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("PROSEFORGE_ROOT", str(tmp_path / "engine"))
    sub = tmp_path / "sub"
    sub.mkdir()
    cfg_file = _write_config(
        sub / "agent.yaml",
        """paths:
  proseforge_root: ${PROSEFORGE_ROOT}
  workspace_root: ./ws
project:
  slug: demo
  title: Demo
""",
    )
    cfg = load_agent_config(cfg_file)
    assert cfg.workspace_root == sub / "ws"
