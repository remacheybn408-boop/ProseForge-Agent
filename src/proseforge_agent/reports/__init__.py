"""Shared report rendering and a registry of named reports.

Reports are the agent's human- and automation-facing output surface: every
report renders to Markdown, JSON, or a terminal summary and always carries a
status and a next action. This package is imported by the CLI; it imports no
workflow code.
"""

from .registry import ReportRegistry, build_command_reference, default_registry
from .render import (
    Report,
    ReportRenderer,
    ReportSection,
    render_json,
    render_markdown,
    render_terminal,
)

__all__ = [
    "Report",
    "ReportSection",
    "ReportRenderer",
    "render_markdown",
    "render_json",
    "render_terminal",
    "ReportRegistry",
    "build_command_reference",
    "default_registry",
]
