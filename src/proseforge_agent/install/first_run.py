"""First-run onboarding for portable agent workspaces."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class FirstRunResult:
    """Artifacts produced by first-run initialization."""

    config_path: Path
    workspace_path: Path
    provider_stub_path: Path
    doctor_report_path: Path
    mode: str
    status: str = "initialized"
    written_artifacts: list[Path] | None = None


class FirstRunWizard:
    """Create a minimal non-destructive ProseForge Agent workspace."""

    def __init__(self, root: str | Path, app_dirs=None, doctor=None) -> None:
        self.root = Path(root)
        self.app_dirs = app_dirs
        self.doctor = doctor

    def run(self, inputs: dict) -> FirstRunResult:
        mode = "native" if inputs.get("native") else "portable"
        config_path = self.root / "config.yaml"
        workspace_path = self.root / "workspace"
        provider_stub_path = self.root / "providers.local.yaml"
        doctor_report_path = self.root / "doctor-report.md"
        if config_path.exists():
            return FirstRunResult(
                config_path=config_path,
                workspace_path=workspace_path,
                provider_stub_path=provider_stub_path,
                doctor_report_path=doctor_report_path,
                mode=mode,
                status="already_initialized",
                written_artifacts=[],
            )

        written: list[Path] = []
        for directory in (
            self.root,
            workspace_path,
            workspace_path / "projects",
            workspace_path / "memory",
            workspace_path / "runs",
            self.root / "logs",
            self.root / "cache",
        ):
            directory.mkdir(parents=True, exist_ok=True)
            written.append(directory)

        proseforge_root = inputs.get("proseforge_root") or "${PROSEFORGE_ROOT}"
        config = {
            "proseforge_root": proseforge_root,
            "workspace": "${PROSEFORGE_AGENT_WORKSPACE:-.pf-agent}/workspace",
            "providers": "${PROSEFORGE_AGENT_WORKSPACE:-.pf-agent}/providers.local.yaml",
            "mode": mode,
        }
        config_path.write_text(yaml.safe_dump(config, sort_keys=True, allow_unicode=True), encoding="utf-8")
        provider_stub_path.write_text(
            "# Local provider profiles. Store raw keys in the secret backend, not here.\nproviders: {}\n",
            encoding="utf-8",
        )
        doctor_report_path.write_text("# First Run Doctor\n\n- status: pending\n", encoding="utf-8")
        written.extend([config_path, provider_stub_path, doctor_report_path])

        return FirstRunResult(
            config_path=config_path,
            workspace_path=workspace_path,
            provider_stub_path=provider_stub_path,
            doctor_report_path=doctor_report_path,
            mode=mode,
            written_artifacts=written,
        )


__all__ = ["FirstRunResult", "FirstRunWizard"]
