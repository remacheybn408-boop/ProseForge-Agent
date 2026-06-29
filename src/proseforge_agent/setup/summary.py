"""Human-facing setup summary rendering."""

from __future__ import annotations


def render_setup_lines(result) -> list[str]:
    lines = [
        f"mode: {result.mode}",
        f"config: {result.config_path}",
        f"workspace: {result.workspace_path}",
    ]
    lines.extend(
        f"provider {provider.name}: {provider.status}"
        + (f" ({provider.reason})" if provider.reason else "")
        for provider in result.providers
    )
    if result.warnings:
        lines.extend(f"warning: {warning}" for warning in result.warnings)
    if result.errors:
        lines.extend(f"error: {error}" for error in result.errors)
    lines.extend(f"next: {step}" for step in result.next_steps)
    return lines


__all__ = ["render_setup_lines"]
