import json
from pathlib import Path

import pytest

from proseforge_agent.chat.memory import ChatMemoryExtractor, MemoryCandidate
from proseforge_agent.cli import main
from proseforge_agent.errors import ConfigurationError


FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "chat-memory-and-user-preferences"
    / "turns.jsonl"
)


def test_memory_extractor_detects_global_preference():
    candidates = ChatMemoryExtractor().extract("以后默认中文回答")
    assert len(candidates) == 1
    candidate = candidates[0]
    assert isinstance(candidate, MemoryCandidate)
    assert candidate.scope == "global"
    assert candidate.status == "candidate"
    assert candidate.kind == "preference"


def test_project_preferences_go_to_project_queue(tmp_path):
    extractor = ChatMemoryExtractor()
    candidates = extractor.write_candidates(
        tmp_path,
        "这个项目以后用冷峻语气",
        project_slug="demo",
    )
    assert candidates[0].scope == "project"
    global_queue = tmp_path / "memory_candidates" / "global.jsonl"
    project_queue = tmp_path / "memory_candidates" / "projects" / "demo.jsonl"
    assert not global_queue.exists()
    assert project_queue.exists()


def test_project_memory_queue_rejects_path_traversal(tmp_path):
    with pytest.raises(ConfigurationError, match="unsafe project slug"):
        ChatMemoryExtractor().write_candidates(
            tmp_path,
            "remember project default tone",
            project_slug="../../evil",
        )

    assert not (tmp_path / "evil.jsonl").exists()


def test_candidates_are_not_accepted_canon_writes(tmp_path):
    candidates = ChatMemoryExtractor().write_candidates(
        tmp_path,
        "remember I prefer concise reports",
    )
    assert candidates[0].status == "candidate"
    assert candidates[0].kind == "preference"
    assert not (tmp_path / "memory.sqlite").exists()


def test_memory_fixture_extracts_global_and_project_preferences():
    rows = [
        json.loads(line)
        for line in FIXTURE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    extractor = ChatMemoryExtractor()
    scopes = [
        candidate.scope
        for row in rows
        for candidate in extractor.extract(row["text"], project_slug=row.get("project_slug"))
    ]
    assert scopes == ["global", "project"]


def test_show_memory_candidates_cli_separates_queues(capsys):
    code = main(
        [
            "chat",
            "--message",
            "以后默认中文回答",
            "--provider",
            "fake",
            "--show-memory-candidates",
        ]
    )
    out = capsys.readouterr().out
    assert code == 0
    assert "Memory Candidates" in out
    assert "global" in out
    assert "candidate" in out
    assert "Agent Chat" not in out
