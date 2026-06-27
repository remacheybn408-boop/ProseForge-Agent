import pytest

from proseforge_agent.memory import MemoryItem, MemoryStore
from proseforge_agent.retrieval.index import MemoryIndex
from proseforge_agent.retrieval.router import RetrievalRequest, RetrievalRouter


@pytest.fixture
def router(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite")
    store.add(MemoryItem(project_slug="demo", type="canon_fact", text="The hero fears deep water.", source="c:1", tags=["water"]))
    store.add(MemoryItem(project_slug="demo", type="reader_promise", text="The old case will be solved.", source="c:2", tags=["case"]))
    store.add(MemoryItem(project_slug="demo", type="style", text="Keep sentences short.", source="c:3"))
    return RetrievalRouter(MemoryIndex(store))


def test_intent_maps_to_query_without_manual_query(router):
    items = router.route(RetrievalRequest(project_slug="demo", intent="chapter_draft"))
    assert items


def test_results_ranked_by_score_descending(router):
    items = router.route(
        RetrievalRequest(project_slug="demo", intent="chapter_draft", query="water case")
    )
    scores = [item.score for item in items]
    assert scores == sorted(scores, reverse=True)


def test_keyword_match_scores_higher(router):
    items = router.route(
        RetrievalRequest(project_slug="demo", intent="chapter_draft", query="water")
    )
    top = items[0]
    assert "water" in top.text.lower()
    assert top.score > 0


def test_explicit_query_overrides_intent(router):
    items = router.route(
        RetrievalRequest(project_slug="demo", intent="review", query="case")
    )
    assert items[0].score > 0
    assert "case" in items[0].text.lower()


def test_each_routed_item_has_inclusion_reason(router):
    items = router.route(
        RetrievalRequest(project_slug="demo", intent="chapter_draft", query="water")
    )
    assert all(item.reason_included for item in items)
