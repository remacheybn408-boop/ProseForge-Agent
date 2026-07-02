"""README localization + drift tests (Task 193)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_drift():
    spec = importlib.util.spec_from_file_location(
        "pf_i18n_drift", REPO_ROOT / "docs" / "i18n" / "drift.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclass needs the module registered
    spec.loader.exec_module(module)
    return module


compare_readmes = _load_drift().compare_readmes

EN = REPO_ROOT / "README.md"
ZH = REPO_ROOT / "README.zh-CN.md"


def test_readmes_have_matching_section_structure():
    report = compare_readmes(EN, ZH)
    assert not report.extra_in_source, f"sections missing in translation: {report.extra_in_source}"
    assert not report.extra_in_translation, f"sections not in source: {report.extra_in_translation}"


def test_switcher_block_is_first_line_of_both_readmes():
    for path in (EN, ZH):
        first = path.read_text(encoding="utf-8").splitlines()[0]
        assert first.startswith(">")
        assert "English" in first
        assert "中文" in first


def test_switcher_links_use_relative_paths():
    for path in (EN, ZH):
        first = path.read_text(encoding="utf-8").splitlines()[0]
        assert "README.md" in first
        assert "README.zh-CN.md" in first
        assert "http" not in first


def test_glossary_covers_core_terms():
    glossary = (REPO_ROOT / "docs" / "i18n" / "glossary.md").read_text(encoding="utf-8")
    for term in ("Agent", "Provider", "Skill", "Middleware", "Workspace"):
        assert term in glossary


def test_chinese_readme_has_no_todo_or_lorem_markers():
    text = ZH.read_text(encoding="utf-8")
    for marker in ("FIXME", "lorem ipsum", "待翻译", "TRANSLATE-ME"):
        assert marker not in text
