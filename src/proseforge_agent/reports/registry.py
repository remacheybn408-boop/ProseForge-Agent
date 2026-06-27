"""Named report builders.

The registry maps a report name to a builder so the CLI and other callers can
ask for a report by name without knowing how it is assembled. The built-in
``command-reference`` report documents the CLI command groups, keeping the
operator surface self-describing.
"""

from __future__ import annotations

from collections.abc import Callable

from ..errors import ConfigurationError
from .render import Report, ReportSection

ReportBuilder = Callable[..., Report]


def build_command_reference(groups: dict[str, dict]) -> Report:
    """Document each CLI command group, its inputs, and its artifacts."""
    sections: list[ReportSection] = []
    for name, spec in groups.items():
        sections.append(
            ReportSection(
                heading=f"{name} — {spec.get('help', '')}",
                lines=[
                    f"inputs: {spec.get('inputs', '(none)')}",
                    f"artifacts: {spec.get('artifacts', '(none)')}",
                ],
            )
        )
    return Report(
        title="ProseForge Agent Command Reference",
        status="ok",
        next_action="Run `pf-agent <group> --help` for command details",
        sections=sections,
        data={"groups": sorted(groups)},
    )


class ReportRegistry:
    """Resolve a report name to a built :class:`Report`."""

    def __init__(self) -> None:
        self._builders: dict[str, ReportBuilder] = {}

    def register(self, name: str, builder: ReportBuilder) -> None:
        self._builders[name] = builder

    def names(self) -> list[str]:
        return sorted(self._builders)

    def build(self, name: str, **kwargs) -> Report:
        builder = self._builders.get(name)
        if builder is None:
            raise ConfigurationError(
                f"unknown report {name!r}; known reports: {self.names()}"
            )
        return builder(**kwargs)


def default_registry() -> ReportRegistry:
    registry = ReportRegistry()
    registry.register("command-reference", build_command_reference)
    return registry


__all__ = ["ReportRegistry", "build_command_reference", "default_registry"]
