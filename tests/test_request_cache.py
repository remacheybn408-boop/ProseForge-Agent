"""Request cache tests (Task 126)."""

from __future__ import annotations

import json

from proseforge_agent.agent.audit import AuditTrailStore
from proseforge_agent.agent.request_cache import RequestCache, RequestCacheKey
from proseforge_agent.cli import main


def test_request_cache_key_uses_prompt_provider_evidence_tools_and_temperature():
    key = RequestCacheKey.build(
        prompt="hello",
        system_prompt_version="prompt@1",
        provider="fake",
        model="fake",
        evidence=["ev1"],
        tool_results=[{"tool": "search", "output": "x"}],
        temperature=0.2,
    )
    changed = RequestCacheKey.build(
        prompt="hello",
        system_prompt_version="prompt@1",
        provider="fake",
        model="fake",
        evidence=["ev1"],
        tool_results=[{"tool": "search", "output": "x"}],
        temperature=0.8,
    )

    assert key.value != changed.value
    assert key.provider == "fake"
    assert key.model == "fake"


def test_request_cache_hit_stats_clear_and_audit(tmp_path):
    cache = RequestCache(tmp_path)
    audit = AuditTrailStore(tmp_path)
    key = RequestCacheKey.build(
        prompt="hello",
        system_prompt_version="prompt@1",
        provider="fake",
        model="fake",
        evidence=[],
        tool_results=[],
        temperature=0.0,
    )

    assert cache.get(key) is None
    cache.put(key, {"text": "cached"})
    hit = cache.get(key, audit_store=audit, session_id="session_001")

    assert hit is not None
    assert hit.payload == {"text": "cached"}
    assert hit.cache_hit is True
    assert cache.stats()["entries"] == 1
    audit_payload = json.loads((tmp_path / "audit" / "session_001.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert audit_payload["final_action"] == "cache_hit"
    assert key.value in audit_payload["model_output"]

    assert cache.clear() == 1
    assert cache.stats()["entries"] == 0


def test_request_cache_cli_list_stats_clear(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cache = RequestCache(".pf-agent")
    key = RequestCacheKey.build(
        prompt="hello",
        system_prompt_version="prompt@1",
        provider="fake",
        model="fake",
        evidence=[],
        tool_results=[],
        temperature=0.0,
    )
    cache.put(key, {"text": "cached"})

    assert main(["cache", "list"]) == 0
    assert main(["cache", "stats"]) == 0
    assert main(["cache", "clear"]) == 0

    out = capsys.readouterr().out
    assert "Request Cache" in out
    assert "entries=1" in out
    assert "cleared=1" in out
