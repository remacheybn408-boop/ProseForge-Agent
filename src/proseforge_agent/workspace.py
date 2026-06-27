"""Resolve and create the Agent workspace directory layout.

The workspace holds everything the Agent owns that is separate from the
ProseForge engine: per-project state, generated plans and workbooks, evidence
packs, workflow run state, prompts, drafts, reports, and logs. The SQLite
``agent.db`` lives at the workspace root, but its schema is owned by the memory
task; ``ensure()`` only creates directories, never that file.

All directory names are declared explicitly here so the layout is the same on
Windows, macOS, and Linux.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import AgentConfig

# Required by Task 02 acceptance.
REQUIRED_SUBDIRS: tuple[str, ...] = (
    "projects",
    "phase_plans",
    "daily_workbooks",
    "evidence_packs",
    "workflow_runs",
    "reports",
    "logs",
)

# Additional directories from the architecture/02 workspace layout.
_EXTRA_SUBDIRS: tuple[str, ...] = (
    "prompts",
    "drafts",
)

_ALL_SUBDIRS: tuple[str, ...] = REQUIRED_SUBDIRS + _EXTRA_SUBDIRS

_AGENT_DB_NAME = "agent.db"


@dataclass(frozen=True)
class WorkspaceLayout:
    """Explicit, OS-independent map of the Agent workspace directories."""

    workspace_root: Path

    @classmethod
    def from_config(cls, config: "AgentConfig") -> "WorkspaceLayout":
        """Build a layout from a loaded :class:`AgentConfig`."""
        return cls(workspace_root=config.workspace_root)

    def _sub(self, name: str) -> Path:
        return self.workspace_root / name

    @property
    def projects(self) -> Path:
        return self._sub("projects")

    @property
    def phase_plans(self) -> Path:
        return self._sub("phase_plans")

    @property
    def daily_workbooks(self) -> Path:
        return self._sub("daily_workbooks")

    @property
    def evidence_packs(self) -> Path:
        return self._sub("evidence_packs")

    @property
    def workflow_runs(self) -> Path:
        return self._sub("workflow_runs")

    @property
    def prompts(self) -> Path:
        return self._sub("prompts")

    @property
    def drafts(self) -> Path:
        return self._sub("drafts")

    @property
    def reports(self) -> Path:
        return self._sub("reports")

    @property
    def logs(self) -> Path:
        return self._sub("logs")

    @property
    def agent_db(self) -> Path:
        """Path to the Agent SQLite database (file created by the memory task)."""
        return self._sub(_AGENT_DB_NAME)

    def ensure(self) -> "WorkspaceLayout":
        """Create the workspace root and all subdirectories. Idempotent."""
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        for name in _ALL_SUBDIRS:
            self._sub(name).mkdir(parents=True, exist_ok=True)
        return self


__all__ = ["WorkspaceLayout", "REQUIRED_SUBDIRS"]
