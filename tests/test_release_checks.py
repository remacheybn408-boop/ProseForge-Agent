from pathlib import Path

from proseforge_agent.release import ReleaseChecker

_REPO_ROOT = Path(__file__).parents[1]

_REQUIRED_CHECKS = {
    "provider_certification",
    "memory_audit",
    "docs_examples",
    "fake_demo",
}


def test_release_passes_with_full_repo():
    report = ReleaseChecker(_REPO_ROOT).run()
    assert report.passed is True


def test_release_fails_when_docs_missing(tmp_path):
    report = ReleaseChecker(tmp_path).run()
    assert report.passed is False
    docs = next(c for c in report.checks if c.name == "docs_examples")
    assert docs.passed is False


def test_release_lists_all_required_checks():
    report = ReleaseChecker(_REPO_ROOT).run()
    assert _REQUIRED_CHECKS <= {c.name for c in report.checks}


def test_release_report_renders():
    report = ReleaseChecker(_REPO_ROOT).run()
    text = report.render()
    for name in _REQUIRED_CHECKS:
        assert name in text
