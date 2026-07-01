"""Skill specification and registry tests (Task 174)."""

from __future__ import annotations

from pathlib import Path

from proseforge_agent.cli import main
from proseforge_agent.skills import SkillRegistry, SkillValidationError


def test_skill_registry_validates_frontmatter(tmp_path):
    skill_dir = _write_skill(
        tmp_path,
        "demo",
        """
---
name: demo-skill
description: Helps with demo tasks.
triggers:
  - demo
version: 1.0.0
permissions:
  - read_only
files:
  - SKILL.md
provenance:
  source: local-test
enabled: true
---

# Demo Skill

Follow the demo procedure.
""",
    )

    records = SkillRegistry.discover([skill_dir])

    assert records[0].name == "demo-skill"
    assert records[0].version == "1.0.0"
    assert records[0].enabled is True


def test_skill_registry_reports_missing_required_fields(tmp_path):
    skill_dir = _write_skill(
        tmp_path,
        "bad",
        """
---
name: bad-skill
---

# Bad Skill
""",
    )

    try:
        SkillRegistry.discover([skill_dir])
    except SkillValidationError as exc:
        assert "description" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("missing fields should fail")


def test_skill_registry_rejects_duplicate_names(tmp_path):
    first = _write_skill(tmp_path, "one", _skill_text("same-skill"))
    second = _write_skill(tmp_path, "two", _skill_text("same-skill"))

    try:
        SkillRegistry.discover([first, second])
    except SkillValidationError as exc:
        assert "duplicate" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("duplicates should fail")


def test_skill_registry_rejects_unsafe_file_paths(tmp_path):
    skill_dir = _write_skill(tmp_path, "unsafe", _skill_text("unsafe-skill", files=["../secret.txt"]))

    try:
        SkillRegistry.discover([skill_dir])
    except SkillValidationError as exc:
        assert "escapes" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("unsafe files should fail")


def test_skills_cli_list(capsys):
    assert main(["skills", "list"]) == 0

    out = capsys.readouterr().out
    assert "Skills" in out


def _write_skill(root: Path, name: str, text: str) -> Path:
    skill_dir = root / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(text.strip(), encoding="utf-8")
    return skill_dir


def _skill_text(name: str, files: list[str] | None = None) -> str:
    files = files or ["SKILL.md"]
    files_yaml = "\n".join(f"  - {item}" for item in files)
    return f"""
---
name: {name}
description: Helps with demo tasks.
triggers:
  - demo
version: 1.0.0
permissions:
  - read_only
files:
{files_yaml}
provenance:
  source: local-test
---

# {name}
"""
