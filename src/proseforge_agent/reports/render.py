"""Shared report rendering: Markdown, JSON, and terminal summaries.

Every operator-facing report carries a status and a next action, so a human or
an automation can tell at a glance what happened and what to do next. The JSON
form is deterministic (fixed structure, sorted keys at the CLI boundary) so it
is stable for automation; the terminal form is a compact one-screen summary.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from ..errors import ConfigurationError

VALID_FORMATS: tuple[str, ...] = ("markdown", "json", "terminal")


@dataclass
class ReportSection:
    """One titled block of report lines."""

    heading: str
    lines: list[str] = field(default_factory=list)


@dataclass
class Report:
    """A renderable operator report with status and next action."""

    title: str
    status: str
    next_action: str
    sections: list[ReportSection] = field(default_factory=list)
    data: dict = field(default_factory=dict)


def render_markdown(report: Report) -> str:
    lines = [
        f"# {report.title}",
        "",
        f"**Status:** {report.status}",
        f"**Next action:** {report.next_action}",
        "",
    ]
    for section in report.sections:
        lines.append(f"## {section.heading}")
        lines += [f"- {line}" for line in section.lines] or ["_(none)_"]
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_json(report: Report) -> dict:
    return {
        "title": report.title,
        "status": report.status,
        "next_action": report.next_action,
        "sections": [
            {"heading": section.heading, "lines": list(section.lines)}
            for section in report.sections
        ],
        "data": report.data,
    }


def render_terminal(report: Report) -> str:
    lines = [f"[{report.status}] {report.title}"]
    for section in report.sections:
        lines.append(f"  {section.heading}:")
        lines += [f"    - {line}" for line in section.lines]
    lines.append(f"-> {report.next_action}")
    return "\n".join(lines)


class ReportRenderer:
    """Render a report in a requested format."""

    def render(self, report: Report, fmt: str = "terminal") -> str:
        if fmt == "markdown":
            return render_markdown(report)
        if fmt == "terminal":
            return render_terminal(report)
        if fmt == "json":
            return json.dumps(
                render_json(report), ensure_ascii=False, indent=2, sort_keys=True
            )
        raise ConfigurationError(
            f"unknown report format {fmt!r}; expected one of {VALID_FORMATS}"
        )


__all__ = [
    "VALID_FORMATS",
    "ReportSection",
    "Report",
    "render_markdown",
    "render_json",
    "render_terminal",
    "ReportRenderer",
]
