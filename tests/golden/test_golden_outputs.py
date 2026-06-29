"""Golden snapshot tests for deterministic outputs (Task 67).

Each test renders a deterministic, network-free output with the canonical fakes
and diffs it against a stored UTF-8 snapshot. A drifted output fails with a
readable diff naming the snapshot.
"""

from __future__ import annotations

import difflib
import json
from pathlib import Path

from proseforge_agent.llm.base import Message, ProviderRequest
from proseforge_agent.memory.store import MemoryStore
from proseforge_agent.retrieval.evidence import EvidencePackBuilder
from proseforge_agent.retrieval.router import EvidenceItem
from proseforge_agent.testing.fakes import FakeProvider

SNAPSHOTS = Path(__file__).parent / "snapshots"


class _FixedRouter:
    """Return a fixed, ranked evidence set so the pack is deterministic."""

    def __init__(self, items: list[EvidenceItem]) -> None:
        self._items = items

    def route(self, request) -> list[EvidenceItem]:
        return list(self._items)


def golden_evidence_pack_markdown() -> str:
    items = [
        EvidenceItem(
            text="主角名叫沈砚，左手有一道旧伤。",
            source="bible:characters",
            type="canon_fact",
            score=0.95,
            reason_included="hard canon",
        ),
        EvidenceItem(
            text="读者被许诺第三章揭示血玉的来历。",
            source="promise:ch3",
            type="reader_promise",
            score=0.88,
            reason_included="active reader promise",
        ),
        EvidenceItem(
            text="叙述语气保持冷峻、克制。",
            source="style:guide",
            type="style",
            score=0.70,
            reason_included="style rule",
        ),
    ]
    builder = EvidencePackBuilder(MemoryStore(":memory:"), router=_FixedRouter(items))
    pack = builder.build("demo", "draft_chapter", chapter_no=3, token_budget=1000)
    return builder.render_markdown(pack)


def golden_chapter_run() -> dict:
    provider = FakeProvider()
    stages = [
        ("planner", "为第三章草拟大纲"),
        ("drafter", "写出第三章初稿开头"),
        ("reviewer", "审阅第三章初稿"),
    ]
    run = []
    for role, prompt in stages:
        result = provider.generate(
            ProviderRequest(role=role, messages=[Message(role="user", content=prompt)])
        )
        run.append(
            {
                "stage": role,
                "text": result.text,
                "prompt_tokens": result.usage.prompt_tokens,
                "completion_tokens": result.usage.completion_tokens,
            }
        )
    return {"chapter": 3, "stages": run}


def _assert_matches_snapshot(actual: str, name: str) -> None:
    snapshot_path = SNAPSHOTS / name
    expected = snapshot_path.read_text(encoding="utf-8")
    if actual != expected:
        diff = "\n".join(
            difflib.unified_diff(
                expected.splitlines(),
                actual.splitlines(),
                fromfile=f"snapshot/{name}",
                tofile="actual",
                lineterm="",
            )
        )
        raise AssertionError(f"golden output drifted from {name}:\n{diff}")


def test_golden_fake_provider_chapter_run_matches_snapshot():
    actual = json.dumps(golden_chapter_run(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    _assert_matches_snapshot(actual, "chapter_run.json")


def test_golden_evidence_pack_matches_snapshot():
    _assert_matches_snapshot(golden_evidence_pack_markdown(), "evidence_pack.md")
