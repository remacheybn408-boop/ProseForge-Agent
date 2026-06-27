import dataclasses

import pytest

from proseforge_agent.chapter.accept import (
    AcceptanceError,
    AcceptanceRecord,
    ChapterAcceptor,
)
from proseforge_agent.chapter.context import ChapterContextPackage
from proseforge_agent.chapter.draft import ChapterDraft
from proseforge_agent.chapter.review import ChapterReviewer, ReviewedChapter
from proseforge_agent.chapter.rewrite import RewritePlanner, Rewriter
from proseforge_agent.llm.fake import FakeProvider
from proseforge_agent.retrieval.evidence import EvidencePack


def _provider():
    return FakeProvider(name="fake", model="fake-1")


def _context(*, target_length=2000, gates=None, sources=None):
    return ChapterContextPackage(
        project_slug="demo",
        chapter_no=1,
        roadmap_entry={"chapter_no": 1, "title": "启程"},
        evidence_pack=EvidencePack(project_slug="demo", intent="chapter_draft"),
        previous_summary="",
        target_length=target_length,
        scene_beats=["主角接到密信", "雨夜离城"],
        constraints=["不得提前揭示反派身份"],
        gates=gates or ["建立主角动机"],
        source_references=sources or ["roadmap:chapter:1", "bible:canon"],
    )


def _draft(*, used_evidence=("bible:canon",), word_count=2500):
    return ChapterDraft(
        manuscript="正文 " * max(word_count, 1),
        scene_summaries=["主角接到密信"],
        used_evidence=list(used_evidence),
        word_count=word_count,
    )


def _reviewed(*, used_evidence=("bible:canon",), word_count=2500, target_length=2000):
    draft = _draft(used_evidence=used_evidence, word_count=word_count)
    context = _context(target_length=target_length)
    review = ChapterReviewer(_provider()).review(draft, context)
    return ReviewedChapter(
        project_slug="demo", chapter_no=1, draft=draft, context=context, review=review
    )


@pytest.fixture
def chapter_run():
    # All gates pass by default (evidence present, draft long enough).
    return _reviewed(used_evidence=("bible:canon",), word_count=2500, target_length=2000)


def test_failed_gate_requires_audit_reason_for_force_accept(chapter_run):
    chapter_run.review.gates["continuity"] = "fail"
    with pytest.raises(AcceptanceError, match="audit reason"):
        ChapterAcceptor().accept(chapter_run, force=True, reason="")


def test_failed_gate_blocks_normal_acceptance(chapter_run):
    chapter_run.review.gates["continuity"] = "fail"
    with pytest.raises(AcceptanceError):
        ChapterAcceptor().accept(chapter_run, force=False, reason="")


def test_force_accept_with_reason_records_audit(chapter_run):
    chapter_run.review.gates["continuity"] = "fail"
    record = ChapterAcceptor().accept(
        chapter_run, force=True, reason="manual editorial override"
    )
    assert record.forced is True
    assert record.reason == "manual editorial override"


def test_passing_chapter_accepts_without_force(chapter_run):
    record = ChapterAcceptor().accept(chapter_run)
    assert isinstance(record, AcceptanceRecord)
    assert record.forced is False
    assert record.final_text == chapter_run.draft.manuscript


def test_accept_locks_final_text(chapter_run):
    record = ChapterAcceptor().accept(chapter_run)
    with pytest.raises(dataclasses.FrozenInstanceError):
        record.final_text = "tampered"


def test_accept_creates_memory_update_candidates(chapter_run):
    record = ChapterAcceptor().accept(chapter_run)
    assert record.memory_update_candidates


def test_rewrite_plan_prioritizes_continuity_over_prose():
    run = _reviewed(used_evidence=(), word_count=10, target_length=2000)
    # missing evidence -> continuity fail; short -> prose_quality warning
    plan = RewritePlanner(_provider()).plan(run.review, run.context)
    categories = [item.issue_id.split(":")[0] for item in plan.items]
    assert "continuity" in categories
    continuity_item = next(i for i in plan.items if i.issue_id.startswith("continuity"))
    # prose_quality is a taste warning -> deferred, not an active high-priority item
    assert all(i.priority >= continuity_item.priority for i in plan.items)
    assert any(d.issue_id.startswith("prose_quality") for d in plan.deferred)


def test_rewrite_preserves_source_and_change_summary():
    run = _reviewed(used_evidence=(), word_count=10, target_length=2000)
    plan = RewritePlanner(_provider()).plan(run.review, run.context)
    revised = Rewriter(_provider()).apply(plan, run.draft, run.context)
    assert revised.source_manuscript == run.draft.manuscript
    assert revised.change_summary


def test_every_rewrite_item_has_acceptance_criteria():
    run = _reviewed(used_evidence=(), word_count=10, target_length=2000)
    plan = RewritePlanner(_provider()).plan(run.review, run.context)
    assert plan.items
    assert all(item.acceptance_criteria for item in plan.items)
