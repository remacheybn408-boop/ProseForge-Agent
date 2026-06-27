import pytest

from proseforge_agent.daily import DailyWorkbookEngine, ProjectState


@pytest.fixture
def project_state():
    return ProjectState(
        slug="demo", target_chapters=12, completed_chapters=2, current_chapter=3
    )


def test_daily_workbook_recommends_next_state_based_action(project_state):
    workbook = DailyWorkbookEngine().generate(project_state, date="2026-08-15")
    assert workbook.date == "2026-08-15"
    assert workbook.recommendation.next_action
    assert workbook.acceptance_checklist


def test_workbook_has_all_required_blocks(project_state):
    wb = DailyWorkbookEngine().generate(project_state, date="2026-08-15")
    assert wb.objective
    assert wb.reading_context
    assert wb.build_block
    assert wb.verification_block
    assert wb.integration_block
    assert wb.closeout
    assert wb.acceptance_checklist
    assert wb.next_day_risk


def test_render_markdown_includes_date_and_objective(project_state):
    engine = DailyWorkbookEngine()
    wb = engine.generate(project_state, date="2026-08-15")
    md = engine.render_markdown(wb)
    assert "2026-08-15" in md
    assert wb.objective in md


def test_render_json_has_recommendation_and_checklist(project_state):
    engine = DailyWorkbookEngine()
    wb = engine.generate(project_state, date="2026-08-15")
    data = engine.render_json(wb)
    assert data["recommendation"]["next_action"]
    assert data["acceptance_checklist"]


def test_weekly_rollup_summarizes_days(project_state):
    engine = DailyWorkbookEngine()
    days = [
        engine.generate(project_state, date="2026-08-15"),
        engine.generate(project_state, date="2026-08-16"),
    ]
    rollup = engine.rollup_week(days, week_start="2026-08-15")
    assert rollup.days == ["2026-08-15", "2026-08-16"]
    assert len(rollup.objectives) == 2


def test_closeout_advances_state(project_state):
    advanced = DailyWorkbookEngine().apply_closeout(project_state, completed=True)
    assert advanced.completed_chapters == project_state.completed_chapters + 1
    assert advanced.current_chapter == project_state.current_chapter + 1
