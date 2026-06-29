"""Tests for the task planner and TODO tracking (Task 69)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from proseforge_agent.agent.planner import PlanError, TaskItem, TaskList, TaskPlanner

FIXTURE = (
    Path(__file__).parent / "fixtures" / "task-planner-and-todo" / "plan_example.json"
)


def test_decompose_produces_ordered_subtasks_with_status():
    plan = TaskPlanner().decompose(goal="写一章：审讯堂发现血玉线索")
    assert len(plan.items) >= 2
    assert all(item.status == "pending" for item in plan.items)
    assert plan.next().id == plan.items[0].id


def test_completed_task_is_marked_done_and_unblocks_dependents():
    plan = TaskPlanner().decompose(goal="写一章开头")
    first = plan.items[0]
    second = plan.items[1]
    assert plan.next().id == first.id  # second is blocked by first
    plan.update(first.id, "done")
    assert plan.next().id == second.id


def test_blocked_task_records_reason_and_is_not_silently_skipped():
    plan = TaskPlanner().decompose(goal="写一章开头")
    first = plan.items[0]
    with pytest.raises(PlanError):
        plan.update(first.id, "blocked")  # no reason
    plan.update(first.id, "blocked", reason="缺少角色设定，无法继续")
    assert plan.get(first.id).status == "blocked"
    assert "缺少角色设定" in plan.get(first.id).reason
    # The blocked task is still visible in the plan.
    assert any(item.id == first.id for item in plan.items)


def test_plan_can_be_revised_mid_run():
    plan = TaskPlanner().decompose(goal="写一章开头")
    plan.update(plan.items[0].id, "done")
    statuses_before = {item.id: item.status for item in plan.items}
    plan.add(TaskItem(id="extra", title="补充世界观一致性检查", depends_on=[plan.items[0].id]))
    # Existing task statuses are untouched by the revision.
    for item in plan.items:
        if item.id in statuses_before:
            assert item.status == statuses_before[item.id]
    assert plan.get("extra").status == "pending"


def test_next_returns_none_when_all_tasks_are_done():
    plan = TaskPlanner().decompose(goal="写一章开头")
    for item in plan.items:
        plan.update(item.id, "done")
    assert plan.next() is None


def test_chinese_subtask_titles_round_trip_utf8():
    plan = TaskPlanner().decompose(goal="审讯堂发现血玉线索")
    payload = json.dumps(plan.to_dict(), ensure_ascii=False)
    restored = TaskList.from_dict(json.loads(payload))
    assert restored.items[0].title == plan.items[0].title
    assert "审讯堂" in restored.items[0].title


def test_planner_hook_overrides_default_decomposition():
    def hook(goal, context):
        return [
            TaskItem(id="a", title=f"A:{goal}"),
            TaskItem(id="b", title="B", depends_on=["a"]),
        ]

    plan = TaskPlanner(planner_hook=hook).decompose(goal="x")
    assert [i.id for i in plan.items] == ["a", "b"]


def test_plan_fixture_round_trips():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    plan = TaskList.from_dict(payload)
    assert plan.next().id == "t1-gather"
