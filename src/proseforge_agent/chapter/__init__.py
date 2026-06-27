"""Chapter lifecycle: orchestrate prepare -> draft -> ... -> memory update.

This package composes config, memory, retrieval, llm, engine adapter, and
workflow state into a single, resumable, fully-offline chapter run. It is
imported by the CLI and higher-level orchestration, never by those subsystems.
"""

from .accept import AcceptanceError, AcceptanceRecord, ChapterAcceptor
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
from .review import (
    REVIEW_CATEGORIES,
    ChapterReviewer,
    ReviewedChapter,
    ReviewFinding,
    ReviewPromptBuilder,
    ReviewReport,
)
from .rewrite import (
    RevisedDraft,
    RevisionValidator,
    RewriteItem,
    RewritePlan,
    RewritePlanner,
    RewritePromptBuilder,
    Rewriter,
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
    "REVIEW_CATEGORIES",
    "ReviewFinding",
    "ReviewReport",
    "ReviewedChapter",
    "ReviewPromptBuilder",
    "ChapterReviewer",
    "RewriteItem",
    "RewritePlan",
    "RewritePlanner",
    "RewritePromptBuilder",
    "RevisedDraft",
    "Rewriter",
    "RevisionValidator",
    "AcceptanceError",
    "AcceptanceRecord",
    "ChapterAcceptor",
]
