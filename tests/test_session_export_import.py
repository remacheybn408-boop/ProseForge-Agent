"""Session export/import tests (Task 129)."""

from __future__ import annotations

import json

from proseforge_agent.chat.session import ChatSessionStore
from proseforge_agent.cli import main


def test_session_export_redacts_and_can_exclude_tools_and_evidence(tmp_path):
    store = ChatSessionStore(tmp_path)
    session = store.create(mode="project_chat", project_slug="demo", session_id="session_001")
    store.append_message(
        session.id,
        "assistant",
        "done api_key=sk-secret",
        evidence_refs=["ev-secret"],
        tool_calls=[{"name": "provider", "api_key": "sk-secret"}],
    )

    payload = store.export_bundle(
        session.id,
        include_tools=False,
        include_evidence=False,
        redact=True,
    )
    serialized = json.dumps(payload, ensure_ascii=False)

    assert "sk-secret" not in serialized
    assert payload["messages"][0]["tool_calls"] == []
    assert payload["messages"][0]["evidence_refs"] == []


def test_session_import_round_trips_json_bundle(tmp_path):
    source = ChatSessionStore(tmp_path / "source")
    session = source.create(mode="general_chat", session_id="session_001")
    source.append_message(session.id, "user", "hello")
    bundle = source.export_bundle(session.id)

    target = ChatSessionStore(tmp_path / "target")
    imported = target.import_bundle(bundle)

    assert imported.id == "session_001"
    assert target.load_context(imported.id).messages[0].content == "hello"


def test_session_export_import_cli(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    store = ChatSessionStore(".pf-agent")
    session = store.create(mode="general_chat", session_id="session_001")
    store.append_message(session.id, "user", "hello")
    bundle_path = tmp_path / "session.json"
    bundle_path.write_text(json.dumps(store.export_bundle(session.id)), encoding="utf-8")

    assert main(["session", "export", "session_001", "--format", "json"]) == 0
    assert main(["session", "import", str(bundle_path)]) == 0

    out = capsys.readouterr().out
    assert "Session Export" in out
    assert "Session Import" in out
