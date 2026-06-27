from proseforge_agent.chapter.context import ChapterContextPackage
from proseforge_agent.chapter.draft import ChapterDraft
from proseforge_agent.chapter.review import (
    REVIEW_CATEGORIES,
    ChapterReviewer,
    ReviewReport,
)
from proseforge_agent.llm.fake import FakeProvider
from proseforge_agent.retrieval.evidence import EvidencePack


def _provider():
    return FakeProvider(name="fake", model="fake-1")


def _context(*, target_length=2000):
    return ChapterContextPackage(
        project_slug="demo",
        chapter_no=1,
        roadmap_entry={"chapter_no": 1, "title": "启程"},
        evidence_pack=EvidencePack(project_slug="demo", intent="chapter_draft"),
        target_length=target_length,
        scene_beats=["主角接到密信"],
        gates=["建立主角动机"],
        source_references=["bible:canon"],
    )


def _draft(*, used_evidence=("bible:canon",), word_count=2500):
    return ChapterDraft(
        manuscript="正文 " * max(word_count, 1),
        scene_summaries=["主角接到密信"],
        used_evidence=list(used_evidence),
        word_count=word_count,
    )


def test_review_scores_all_categories():
    report = ChapterReviewer(_provider()).review(_draft(), _context())
    assert isinstance(report, ReviewReport)
    assert set(report.gates) == set(REVIEW_CATEGORIES)


def test_missing_evidence_fails_continuity_gate():
    report = ChapterReviewer(_provider()).review(
        _draft(used_evidence=(), word_count=2500), _context()
    )
    assert report.gates["continuity"] == "fail"
    assert report.recommendation == "needs_revision"


def test_review_separates_objective_from_taste():
    report = ChapterReviewer(_provider()).review(
        _draft(used_evidence=(), word_count=10), _context(target_length=2000)
    )
    assert any(f.is_objective for f in report.findings)
    assert any(not f.is_objective for f in report.findings)


def test_review_cites_sections():
    report = ChapterReviewer(_provider()).review(
        _draft(used_evidence=(), word_count=10), _context()
    )
    assert report.citations
    assert all(f.citation for f in report.findings)


def test_review_repairs_malformed_provider_output():
    # FakeProvider returns non-JSON echo; reviewer must still produce full gates.
    report = ChapterReviewer(_provider()).review(_draft(), _context())
    assert len(report.gates) == len(REVIEW_CATEGORIES)
    assert report.recommendation in {"accept", "needs_revision"}
