from proseforge_agent.memory import MemoryItem, MemoryStore
from proseforge_agent.memory.compact import MemoryCompactor


def _store_with_duplicates(tmp_path):
    store = MemoryStore(tmp_path / "m.sqlite")
    ids = []
    for source in ("chapter:1", "chapter:5", "outline:a"):
        item = store.add(
            MemoryItem(
                project_slug="demo",
                type="canon_fact",
                text="The hero fears deep water.",
                source=source,
            )
        )
        ids.append(item.id)
    return store, ids


def test_compaction_merges_duplicates_and_keeps_source_links(tmp_path):
    store, ids = _store_with_duplicates(tmp_path)
    report = MemoryCompactor(store).compact("demo", dry_run=False)
    assert set(report.included_ids) == set(ids)
    assert set(report.source_coverage) == set(ids)
    summary = store.get(report.summary_id)
    for old_id in ids:
        assert str(old_id) in summary.source
        assert store.get(old_id).status == "superseded"
    assert summary.status == "active"


def test_dry_run_compaction_writes_nothing(tmp_path):
    store, ids = _store_with_duplicates(tmp_path)
    before = len(store.list())
    report = MemoryCompactor(store).compact("demo", dry_run=True)
    assert report.summary_id is None
    assert len(store.list()) == before
    assert all(store.get(i).status == "active" for i in ids)


def test_contradictions_are_preserved(tmp_path):
    store = MemoryStore(tmp_path / "m.sqlite")
    a = store.add(
        MemoryItem(project_slug="demo", type="canon_fact", text="Hero fears water.", source="c:1")
    )
    b = store.add(
        MemoryItem(project_slug="demo", type="canon_fact", text="Hero loves water.", source="c:2")
    )
    report = MemoryCompactor(store).compact("demo", dry_run=False)
    assert store.get(a.id).status == "active"
    assert store.get(b.id).status == "active"
    assert set(report.excluded_ids) == {a.id, b.id}


def test_compaction_report_lists_included_and_excluded(tmp_path):
    store, dup_ids = _store_with_duplicates(tmp_path)
    single = store.add(
        MemoryItem(project_slug="demo", type="canon_fact", text="Unique fact.", source="c:9")
    )
    report = MemoryCompactor(store).compact("demo", dry_run=True)
    assert set(report.included_ids) == set(dup_ids)
    assert single.id in report.excluded_ids
