"""Structured output repair tests (Task 110)."""

from __future__ import annotations

from proseforge_agent.agent.structured_output import (
    repair_structured_output,
    validate_or_repair,
)


SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "count": {"type": "integer"},
    },
    "required": ["title", "count"],
    "additionalProperties": False,
}


def test_structured_output_repair_contract():
    raw = 'Here is the JSON: {"title": "Chapter One", "count": 3,}'

    result = repair_structured_output(raw, SCHEMA)

    assert result.ok is True
    assert result.value == {"title": "Chapter One", "count": 3}
    assert result.repaired is True
    assert result.attempts == 1
    assert "Return only valid JSON" in result.retry_prompt


def test_validate_or_repair_accepts_valid_json_without_repair():
    result = validate_or_repair('{"title": "Clean", "count": 1}', SCHEMA)

    assert result.ok is True
    assert result.value == {"title": "Clean", "count": 1}
    assert result.repaired is False
    assert result.errors == []


def test_repair_returns_structured_schema_error_when_required_field_missing():
    result = validate_or_repair('{"title": "Missing count"}', SCHEMA, max_attempts=2)

    assert result.ok is False
    assert result.value is None
    assert result.attempts == 2
    assert result.errors[0]["type"] == "schema"
    assert result.errors[0]["path"] == "count"
    assert "count" in result.failure_report["missing_required"]


def test_semantic_validation_failure_is_reported():
    result = validate_or_repair(
        '{"title": "Bad", "count": -1}',
        SCHEMA,
        semantic_validator=lambda value: (False, "count must be positive"),
    )

    assert result.ok is False
    assert result.errors[0]["type"] == "semantic"
    assert result.errors[0]["message"] == "count must be positive"
    assert result.retry_prompt
