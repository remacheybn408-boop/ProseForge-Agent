import pytest

from proseforge_agent.errors import ConfigurationError
from proseforge_agent.reports import (
    Report,
    ReportRenderer,
    ReportRegistry,
    ReportSection,
    render_json,
    render_markdown,
    render_terminal,
)
from proseforge_agent.reports.registry import default_registry


def _report():
    return Report(
        title="Demo Report",
        status="ok",
        next_action="run the next command",
        sections=[ReportSection(heading="Summary", lines=["line one", "line two"])],
        data={"count": 2},
    )


def test_render_markdown_has_status_and_next_action():
    md = render_markdown(_report())
    assert "Demo Report" in md
    assert "ok" in md
    assert "run the next command" in md


def test_render_terminal_has_status_and_next_action():
    text = render_terminal(_report())
    assert "ok" in text
    assert "run the next command" in text


def test_render_json_is_stable_and_has_required_keys():
    a = render_json(_report())
    b = render_json(_report())
    assert a == b
    for key in ("title", "status", "next_action", "sections"):
        assert key in a


def test_renderer_rejects_unknown_format():
    with pytest.raises(ConfigurationError):
        ReportRenderer().render(_report(), "xml")


def test_registry_builds_command_reference():
    groups = {
        "provider": {"help": "h", "inputs": "i", "artifacts": "a"},
        "memory": {"help": "h", "inputs": "i", "artifacts": "a"},
    }
    report = default_registry().build("command-reference", groups=groups)
    headings = [s.heading for s in report.sections]
    assert any("provider" in h for h in headings)
    assert any("memory" in h for h in headings)


def test_registry_lists_registered_reports():
    registry = default_registry()
    assert "command-reference" in registry.names()
    with pytest.raises(ConfigurationError):
        registry.build("nope")
