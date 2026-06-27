"""Date-based daily and weekly workbooks.

The workbook engine turns project state into the writer's daily operating
document. It needs no model access and writes nothing itself.
"""

from .recommend import ProjectState, Recommendation, StateRecommender
from .workbook import DailyWorkbook, DailyWorkbookEngine, WeeklyRollup

__all__ = [
    "ProjectState",
    "Recommendation",
    "StateRecommender",
    "DailyWorkbook",
    "DailyWorkbookEngine",
    "WeeklyRollup",
]
