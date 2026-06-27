import json
from pathlib import Path

import pytest

from proseforge_agent.chapter import (
    ChapterContextPackage,
    ChapterLifecycle,
    ChapterProject,
    ChapterWorkflowError,
)
from proseforge_agent.llm.registry import ProviderRegistry
from proseforge_agent.memory.store import MemoryItem, MemoryStore
from proseforge_agent.workspace import WorkspaceLayout

_FIXTURE_ROADMAP = Path(__file__).parent / "fixtures" / "chapter" / "roadmap.json"

_REGISTRY_DATA = {
    "providers": [{"name": "fake", "kind": "fake", "model": "fake-1"}],
    "roles": {"drafter": "fake"},
    "default_provider": "fake",
}


def _load_roadmap() -> dict:
    return json.loads(_FIXTURE_ROADMAP.read_text(encoding="utf-8"))


def _make_project(tmp_path, *, seed_memory: bool) -> ChapterProject:
    workspace = WorkspaceLayout(workspace_root=tmp_path / "workspace").ensure()
    store = MemoryStore(workspace.agent_db)
    if seed_memory:
        store.add(MemoryItem(project_slug="demo", type="canon_fact", text="主角名叫林远", source="bible:canon"))
        store.add(MemoryItem(project_slug="demo", type="style", text="第三人称冷峻文风", source="bible:style"))
        store.add(MemoryItem(project_slug="demo", type="risk", text="勿提前揭示反派", source="bible:risk"))
    registry = ProviderRegistry.from_dict(_REGISTRY_DATA)
    return ChapterProject(
        slug="demo",
        workspace=workspace,
        store=store,
        registry=registry,
        roadmap=_load_roadmap(),
    )


@pytest.fixture
def fake_project(tmp_path):
    return _make_project(tmp_path, seed_memory=True)


@pytest.fixture
def empty_memory_project(tmp_path):
    return _make_project(tmp_path, seed_memory=False)


def test_chapter_run_produces_draft_and_state_artifacts(fake_project):
    result = ChapterLifecycle(fake_project).run(chapter_no=1, provider_name="fake", until="draft")
    assert result.state == "drafted"
    assert result.artifacts.draft_path.exists()
    assert result.artifacts.context_path.exists()


def test_draft_blocked_without_evidence_pack(empty_memory_project):
    with pytest.raises(ChapterWorkflowError):
        ChapterLifecycle(empty_memory_project).run(chapter_no=1, provider_name="fake", until="draft")


def test_draft_artifacts_include_text_and_metadata(fake_project):
    result = ChapterLifecycle(fake_project).run(chapter_no=1, provider_name="fake", until="draft")
    assert result.artifacts.draft_path.read_text(encoding="utf-8").strip()
    meta = json.loads(result.artifacts.draft_meta_path.read_text(encoding="utf-8"))
    assert meta["used_evidence"]
    assert meta["scene_summaries"]


def test_workflow_run_records_context_and_draft_paths(fake_project):
    from proseforge_agent.workflow.state import WorkflowStateStore

    result = ChapterLifecycle(fake_project).run(chapter_no=1, provider_name="fake", until="draft")
    run = WorkflowStateStore(fake_project.workspace.workflow_runs).load(result.run_id)
    assert str(result.artifacts.context_path) in run.artifacts
    assert str(result.artifacts.draft_path) in run.artifacts


def test_context_package_cites_evidence_sources(fake_project):
    result = ChapterLifecycle(fake_project).run(chapter_no=1, provider_name="fake", until="context")
    assert isinstance(result.context, ChapterContextPackage)
    assert any("bible:" in ref for ref in result.context.source_references)


def test_until_context_stops_at_context_ready(fake_project):
    result = ChapterLifecycle(fake_project).run(chapter_no=1, provider_name="fake", until="context")
    assert result.state == "context_ready"
    assert result.draft is None


def test_full_until_memory_reaches_memory_updated(fake_project):
    result = ChapterLifecycle(fake_project).run(chapter_no=1, provider_name="fake", until="memory")
    assert result.state == "memory_updated"
    summaries = [
        i for i in fake_project.store.list(project_slug="demo") if i.type == "chapter_summary"
    ]
    assert len(summaries) == 1


def test_run_is_deterministic(tmp_path):
    project_a = _make_project(tmp_path / "a", seed_memory=True)
    project_b = _make_project(tmp_path / "b", seed_memory=True)
    draft_a = ChapterLifecycle(project_a).run(chapter_no=1, provider_name="fake", until="draft")
    draft_b = ChapterLifecycle(project_b).run(chapter_no=1, provider_name="fake", until="draft")
    assert draft_a.draft.manuscript == draft_b.draft.manuscript
