from pathlib import Path

from proseforge_agent.config import AgentConfig, ProjectConfig
from proseforge_agent.workspace import REQUIRED_SUBDIRS, WorkspaceLayout


def test_ensure_creates_all_workspace_directories(tmp_path):
    layout = WorkspaceLayout(workspace_root=tmp_path / "ws").ensure()
    assert layout.projects.is_dir()
    assert layout.phase_plans.is_dir()
    assert layout.daily_workbooks.is_dir()
    assert layout.evidence_packs.is_dir()
    assert layout.workflow_runs.is_dir()
    assert layout.reports.is_dir()
    assert layout.logs.is_dir()
    # extras from architecture/02 workspace layout
    assert layout.prompts.is_dir()
    assert layout.drafts.is_dir()
    for name in REQUIRED_SUBDIRS:
        assert (layout.workspace_root / name).is_dir()


def test_ensure_is_idempotent(tmp_path):
    layout = WorkspaceLayout(workspace_root=tmp_path / "ws")
    layout.ensure()
    # second call must not raise on existing directories
    again = layout.ensure()
    assert again.projects.is_dir()


def test_agent_db_path_is_under_workspace_and_not_created(tmp_path):
    layout = WorkspaceLayout(workspace_root=tmp_path / "ws").ensure()
    assert layout.agent_db == (tmp_path / "ws" / "agent.db")
    # the schema is owned by a later task; ensure() must not create the file
    assert not layout.agent_db.exists()


def test_workspace_layout_from_config(tmp_path):
    cfg = AgentConfig(
        proseforge_root=tmp_path / "engine",
        workspace_root=tmp_path / "ws",
        project=ProjectConfig(slug="demo", title="Demo"),
    )
    layout = WorkspaceLayout.from_config(cfg)
    assert layout.workspace_root == tmp_path / "ws"
    assert layout.projects == tmp_path / "ws" / "projects"
    assert Path(tmp_path / "ws") in layout.projects.parents
