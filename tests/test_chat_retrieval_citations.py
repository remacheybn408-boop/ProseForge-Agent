import json
from pathlib import Path

from proseforge_agent.chat.retrieval import (
    ChatEvidence,
    ChatRetrievalResponder,
    render_citations,
)
from proseforge_agent.cli import main


FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "chat-retrieval-and-citations"
    / "memory_seed.json"
)


def test_retrieval_answer_cites_used_evidence():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    evidence = [ChatEvidence.from_dict(item) for item in payload["evidence"]]
    answer = ChatRetrievalResponder(evidence=evidence).answer(
        "昨天写到哪里了？",
        project_slug="demo",
    )
    assert answer.degraded is False
    assert answer.used_evidence_ids == ["ev-1", "ev-2"]
    assert answer.citations[0].source == "memory:chapter-002"
    assert "[ev-1]" in answer.text


def test_no_evidence_is_degraded_and_does_not_invent_canon():
    answer = ChatRetrievalResponder(evidence=[]).answer(
        "昨天写到哪里了？",
        project_slug="demo",
    )
    assert answer.degraded is True
    assert answer.citations == []
    assert answer.used_evidence_ids == []
    assert "canon" not in answer.text.lower()


def test_rendered_citations_are_parseable_source_references():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    evidence = [ChatEvidence.from_dict(item) for item in payload["evidence"][:1]]
    answer = ChatRetrievalResponder(evidence=evidence).answer("继续", project_slug="demo")
    rendered = render_citations(answer)
    assert "degraded=false" in rendered
    assert "ev-1|memory:chapter-002|" in rendered


def test_show_citations_cli_reports_degraded_without_evidence(capsys):
    code = main(
        [
            "chat",
            "--message",
            "昨天写到哪里了？",
            "--project",
            "demo",
            "--provider",
            "fake",
            "--show-citations",
        ]
    )
    out = capsys.readouterr().out
    assert code == 0
    assert "Chat Citations" in out
    assert "degraded=true" in out
