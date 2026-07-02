"""Community and agent docs tests (Task 194)."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(name: str) -> str:
    return (REPO_ROOT / name).read_text(encoding="utf-8")


def test_contributing_document_has_required_sections():
    text = _read("CONTRIBUTING.md")
    for header in [
        "## Local Setup",
        "## Branch Strategy",
        "## TDD Requirement",
        "## Commit Messages",
        "## PR Checklist",
    ]:
        assert header in text, f"missing: {header}"


def test_contributing_references_task_cards_and_tooling():
    text = _read("CONTRIBUTING.md")
    assert "pyproject.toml" in text
    assert "tests/" in text
    assert "docs/superpowers/plans/proseforge-agent-tool/tasks" in text


def test_security_document_lists_reporting_channel_and_triage_sla():
    text = _read("SECURITY.md")
    assert "please do not open a public issue" in text.lower()
    assert "Security Advisories" in text or "security advisory" in text.lower()
    assert "days" in text.lower()


def test_agents_document_lists_forbidden_actions_and_test_command():
    text = _read("AGENTS.md")
    assert "python -m pytest -q" in text
    assert "Forbidden" in text or "forbidden" in text
    assert "PROSEFORGE_ROOT" in text


def test_threat_model_page_exists_and_lists_boundaries():
    text = _read("docs/security/threat-model.md")
    for term in ("permission", "MCP", "redact"):
        assert term.lower() in text.lower()


def test_docs_use_utf8_no_bom():
    for name in ("CONTRIBUTING.md", "SECURITY.md", "AGENTS.md", "docs/security/threat-model.md"):
        raw = (REPO_ROOT / name).read_bytes()
        assert not raw.startswith(b"\xef\xbb\xbf"), f"{name} has a UTF-8 BOM"


def test_docs_reference_only_files_that_exist():
    # Spot-check that key referenced paths actually exist in the repo.
    for name in ("CONTRIBUTING.md", "AGENTS.md"):
        text = _read(name)
        for ref in ("pyproject.toml", "src/proseforge_agent", "tests"):
            if ref in text:
                assert (REPO_ROOT / ref).exists(), f"{name} references missing path {ref}"
