"""Continuity conflict resolver tests (Task 89)."""

from __future__ import annotations

import yaml

from proseforge_agent.cli import main
from proseforge_agent.novel import ContinuityResolver, NovelProjectStore


def _seed_facts(root):
    NovelProjectStore(root).init_project(slug="demo_novel")
    path = root / "projects" / "demo_novel" / "continuity" / "facts.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            {
                "facts": [
                    {"id": "fact_001", "subject": "Lin", "key": "age", "value": "17", "source": "ch_001"},
                    {"id": "fact_002", "subject": "Lin", "key": "age", "value": "19", "source": "ch_002"},
                ]
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def test_continuity_conflict_resolver_contract(tmp_path):
    _seed_facts(tmp_path)
    resolver = ContinuityResolver(tmp_path, slug="demo_novel")
    conflicts = resolver.check()
    assert conflicts[0].id == "conflict_001"
    assert conflicts[0].type == "character_age"
    assert conflicts[0].left["value"] == "17"
    assert conflicts[0].right["value"] == "19"


def test_resolve_keep_right_writes_audit_log(tmp_path):
    _seed_facts(tmp_path)
    resolver = ContinuityResolver(tmp_path, slug="demo_novel")
    resolver.check()
    result = resolver.resolve("conflict_001", action="keep_right")
    facts = yaml.safe_load((tmp_path / "projects" / "demo_novel" / "continuity" / "facts.yaml").read_text(encoding="utf-8"))
    audit = (tmp_path / "projects" / "demo_novel" / "continuity" / "audit.log").read_text(encoding="utf-8")
    assert result["status"] == "ok"
    assert facts["facts"][0]["value"] == "19"
    assert "conflict_001 keep_right" in audit


def test_resolve_mark_intentional_keeps_both_values(tmp_path):
    _seed_facts(tmp_path)
    resolver = ContinuityResolver(tmp_path, slug="demo_novel")
    resolver.check()
    resolver.resolve("conflict_001", action="mark_intentional")
    facts = yaml.safe_load((tmp_path / "projects" / "demo_novel" / "continuity" / "facts.yaml").read_text(encoding="utf-8"))
    assert len(facts["facts"]) == 2
    assert all(fact.get("intentional_conflict") for fact in facts["facts"])


def test_continuity_cli_check_and_resolve(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _seed_facts(tmp_path / ".pf-agent" / "workspace")
    assert main(["continuity", "check", "--slug", "demo_novel"]) == 0
    assert main(["continuity", "resolve", "--slug", "demo_novel", "--conflict", "conflict_001", "--action", "keep_right"]) == 0
    out = capsys.readouterr().out
    assert "Continuity" in out
    assert "conflict_001" in out
