import pytest

from proseforge_agent.memory import MemoryItem, MemoryStore
from proseforge_agent.retrieval.evidence import SECTION_KEYS, EvidencePackBuilder


@pytest.fixture
def memory_store(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite")
    store.add(MemoryItem(project_slug="demo", type="canon_fact", text="The hero fears deep water.", source="chapter:1", tags=["hero", "water"]))
    store.add(MemoryItem(project_slug="demo", type="canon_fact", text="The blood jade fades when it leaves the hero.", source="chapter:9", tags=["jade"]))
    store.add(MemoryItem(project_slug="demo", type="reader_promise", text="The old case will be solved.", source="outline:arc1", tags=["case"]))
    store.add(MemoryItem(project_slug="demo", type="continuity_risk", text="Hero swims easily in chapter 2, contradicting fear of water.", source="review:2", tags=["water"]))
    store.add(MemoryItem(project_slug="demo", type="style", text="Keep sentences short and concrete.", source="style:guide"))
    return store


def test_evidence_pack_keeps_canon_and_warnings_separate(memory_store):
    pack = EvidencePackBuilder(memory_store).build(
        project_slug="demo", intent="chapter_draft", chapter_no=3, token_budget=1200
    )
    assert "hard_canon" in pack.sections
    assert "risk_warnings" in pack.sections
    assert all(item.source for item in pack.items)


def test_sections_always_contains_all_keys(memory_store):
    pack = EvidencePackBuilder(memory_store).build(
        project_slug="demo", intent="chapter_draft", token_budget=1200
    )
    assert set(pack.sections) == set(SECTION_KEYS)


def test_each_included_item_has_source_and_inclusion_reason(memory_store):
    pack = EvidencePackBuilder(memory_store).build(
        project_slug="demo", intent="chapter_draft", token_budget=1200
    )
    assert pack.items
    for item in pack.items:
        assert item.source
        assert item.reason_included


def test_excluded_items_have_exclusion_reason(memory_store):
    pack = EvidencePackBuilder(memory_store).build(
        project_slug="demo", intent="chapter_draft", token_budget=3
    )
    assert pack.excluded
    for item in pack.excluded:
        assert item.reason_excluded


def test_pack_fits_token_budget(memory_store):
    pack = EvidencePackBuilder(memory_store).build(
        project_slug="demo", intent="chapter_draft", token_budget=10
    )
    assert pack.used_tokens <= 10


def test_canon_goes_to_hard_canon_section(memory_store):
    pack = EvidencePackBuilder(memory_store).build(
        project_slug="demo", intent="chapter_draft", token_budget=1200
    )
    assert pack.sections["hard_canon"]
    assert all(i.type == "canon_fact" for i in pack.sections["hard_canon"])


def test_risk_goes_to_warnings_section(memory_store):
    pack = EvidencePackBuilder(memory_store).build(
        project_slug="demo", intent="review", token_budget=1200
    )
    assert pack.sections["risk_warnings"]


def test_render_markdown_cites_sources(memory_store):
    builder = EvidencePackBuilder(memory_store)
    pack = builder.build(project_slug="demo", intent="chapter_draft", token_budget=1200)
    md = builder.render_markdown(pack)
    assert "chapter:1" in md


def test_render_json_has_sections_and_items(memory_store):
    builder = EvidencePackBuilder(memory_store)
    pack = builder.build(project_slug="demo", intent="chapter_draft", token_budget=1200)
    data = builder.render_json(pack)
    assert "sections" in data
    assert "items" in data


def test_empty_store_returns_degraded_pack(tmp_path):
    store = MemoryStore(tmp_path / "empty.sqlite")
    pack = EvidencePackBuilder(store).build(
        project_slug="demo", intent="chapter_draft", token_budget=1200
    )
    assert pack.degraded_reason
    assert set(pack.sections) == set(SECTION_KEYS)
