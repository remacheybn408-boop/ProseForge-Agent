from pathlib import Path

import pytest

from proseforge_agent.errors import MemoryError
from proseforge_agent.memory import MemoryStore
from proseforge_agent.memory.ingest import ArtifactIngestor
from proseforge_agent.memory.review import decide, ingest_candidates

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "proseforge_project"


def test_ingest_chapter_creates_review_candidates_with_sources(tmp_path):
    chapter = tmp_path / "chapter-001.md"
    chapter.write_text(
        "# Chapter 1\nA promise is made at the old bridge.", encoding="utf-8"
    )
    candidates = ArtifactIngestor().scan_file(chapter, project_slug="demo")
    assert candidates[0].source_path == chapter
    assert candidates[0].status == "candidate"


def test_every_candidate_has_source_and_reason():
    candidates = ArtifactIngestor().scan_dir(FIXTURE_DIR, project_slug="demo")
    assert candidates
    for candidate in candidates:
        assert candidate.source_path is not None
        assert candidate.reason


def test_scan_dir_aggregates_multiple_files():
    candidates = ArtifactIngestor().scan_dir(FIXTURE_DIR, project_slug="demo")
    sources = {candidate.source_path.name for candidate in candidates}
    assert {"chapter-001.md", "outline.md"} <= sources


def test_source_kind_and_proposed_type_inferred(tmp_path):
    chapter = tmp_path / "chapter-002.md"
    chapter.write_text("A promise is made.", encoding="utf-8")
    candidate = ArtifactIngestor().scan_file(chapter, project_slug="demo")[0]
    assert candidate.source_kind == "chapter"
    assert candidate.proposed_type == "reader_promise"


def test_dry_run_ingest_writes_nothing(tmp_path):
    store = MemoryStore(tmp_path / "m.sqlite")
    candidates = ArtifactIngestor().scan_dir(FIXTURE_DIR, project_slug="demo")
    result = ingest_candidates(store, candidates, dry_run=True)
    assert result.dry_run is True
    assert result.planned == len(candidates)
    assert store.list() == []


def test_accepted_candidate_becomes_memory_item(tmp_path):
    store = MemoryStore(tmp_path / "m.sqlite")
    candidates = ArtifactIngestor().scan_dir(FIXTURE_DIR, project_slug="demo")
    result = ingest_candidates(store, candidates, dry_run=False)
    assert len(result.created) == len(candidates)
    items = store.list(project_slug="demo")
    assert items
    assert all(item.source for item in items)


def test_rejected_candidate_not_ingested(tmp_path):
    store = MemoryStore(tmp_path / "m.sqlite")
    candidates = ArtifactIngestor().scan_dir(FIXTURE_DIR, project_slug="demo")
    decided = [decide(candidates[0], accepted=False)] + [
        decide(c, accepted=True) for c in candidates[1:]
    ]
    result = ingest_candidates(store, decided, dry_run=False)
    assert len(result.created) == len(candidates) - 1


def test_candidate_without_reason_is_rejected_by_ingest(tmp_path):
    store = MemoryStore(tmp_path / "m.sqlite")
    from proseforge_agent.memory.ingest import IngestionCandidate

    bad = IngestionCandidate(
        project_slug="demo",
        source_path=Path("x.md"),
        source_kind="artifact",
        extracted_text="text",
        proposed_type="canon_fact",
        confidence=0.5,
        reason="",
    )
    with pytest.raises(MemoryError):
        ingest_candidates(store, [bad], dry_run=False)
