from proseforge_agent.daily.recommend import ProjectState, StateRecommender


def _state(**overrides):
    base = dict(slug="demo", target_chapters=12, completed_chapters=2, current_chapter=3)
    base.update(overrides)
    return ProjectState(**base)


def test_drafting_recommended_when_on_track():
    rec = StateRecommender().recommend(_state())
    assert "3" in rec.next_action
    assert "draft" in rec.next_action.lower()


def test_overdue_work_carries_forward():
    rec = StateRecommender().recommend(_state(overdue=True))
    assert rec.carry_over
    assert "overdue" in rec.next_action.lower()


def test_blocked_state_recommends_unblock():
    rec = StateRecommender().recommend(_state(blocked_reason="waiting on outline"))
    assert "outline" in rec.next_action
    assert "unblock" in rec.next_action.lower()


def test_memory_risk_changes_recommendation():
    on_track = StateRecommender().recommend(_state())
    risky = StateRecommender().recommend(_state(memory_risk=["continuity: water"]))
    assert risky.next_action != on_track.next_action
    assert "audit" in risky.next_action.lower()


def test_provider_failure_changes_recommendation():
    rec = StateRecommender().recommend(_state(provider_failed=True))
    assert rec.priority == "critical"
    assert "provider" in rec.next_action.lower()


def test_all_chapters_done_recommends_review():
    rec = StateRecommender().recommend(
        _state(completed_chapters=12, current_chapter=13)
    )
    assert "review" in rec.next_action.lower() or "closeout" in rec.next_action.lower()


def test_recommendation_is_state_based_not_date_based():
    on_track = StateRecommender().recommend(_state())
    blocked = StateRecommender().recommend(_state(blocked_reason="art assets"))
    assert on_track.next_action != blocked.next_action
