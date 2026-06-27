"""Chapter lifecycle: orchestrate prepare -> draft -> ... -> memory update.

This package composes config, memory, retrieval, llm, engine adapter, and
workflow state into a single, resumable, fully-offline chapter run. It is
imported by the CLI and higher-level orchestration, never by those subsystems.
"""

from .context import (
    ChapterContextBuilder,
    ChapterContextPackage,
    ChapterWorkflowError,
)
from .draft import ChapterDraft, ChapterDrafter, DraftPromptBuilder, DraftValidator
from .lifecycle import (
    ChapterArtifacts,
    ChapterLifecycle,
    ChapterProject,
    ChapterRunResult,
)

__all__ = [
    "ChapterWorkflowError",
    "ChapterContextPackage",
    "ChapterContextBuilder",
    "DraftPromptBuilder",
    "ChapterDraft",
    "ChapterDrafter",
    "DraftValidator",
    "ChapterProject",
    "ChapterArtifacts",
    "ChapterRunResult",
    "ChapterLifecycle",
]
