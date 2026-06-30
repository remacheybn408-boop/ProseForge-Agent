"""Structured JSON output validation and repair."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


SemanticValidator = Callable[[dict[str, Any]], tuple[bool, str]]


@dataclass(frozen=True)
class StructuredOutputRepairResult:
    """Result of validating or repairing a structured model output."""

    ok: bool
    value: dict[str, Any] | None
    repaired: bool = False
    attempts: int = 0
    errors: list[dict[str, Any]] = field(default_factory=list)
    retry_prompt: str = ""
    failure_report: dict[str, Any] = field(default_factory=dict)


def validate_or_repair(
    raw_text: str,
    schema: dict[str, Any],
    *,
    semantic_validator: SemanticValidator | None = None,
    max_attempts: int = 3,
) -> StructuredOutputRepairResult:
    """Validate strict JSON first, then attempt deterministic repair."""
    try:
        parsed = _parse_json_object(raw_text)
    except ValueError:
        return repair_structured_output(
            raw_text,
            schema,
            semantic_validator=semantic_validator,
            max_attempts=max_attempts,
        )
    return _validate_result(
        parsed,
        schema,
        semantic_validator=semantic_validator,
        repaired=False,
        attempts=0,
        max_attempts=max_attempts,
    )


def repair_structured_output(
    raw_text: str,
    schema: dict[str, Any],
    *,
    semantic_validator: SemanticValidator | None = None,
    max_attempts: int = 3,
) -> StructuredOutputRepairResult:
    """Repair common malformed JSON and validate it against the schema."""
    retry_prompt = _retry_prompt(schema)
    try:
        repaired_text = _repair_json_text(raw_text)
        parsed = _parse_json_object(repaired_text)
    except ValueError as exc:
        return StructuredOutputRepairResult(
            ok=False,
            value=None,
            repaired=True,
            attempts=max_attempts,
            errors=[{"type": "parse", "path": "", "message": str(exc)}],
            retry_prompt=retry_prompt,
            failure_report={"parse_error": str(exc), "raw_text": raw_text},
        )
    return _validate_result(
        parsed,
        schema,
        semantic_validator=semantic_validator,
        repaired=True,
        attempts=1,
        max_attempts=max_attempts,
    )


def _validate_result(
    value: dict[str, Any],
    schema: dict[str, Any],
    *,
    semantic_validator: SemanticValidator | None,
    repaired: bool,
    attempts: int,
    max_attempts: int,
) -> StructuredOutputRepairResult:
    errors = _schema_errors(value, schema)
    if errors:
        return StructuredOutputRepairResult(
            ok=False,
            value=None,
            repaired=repaired,
            attempts=max_attempts,
            errors=errors,
            retry_prompt=_retry_prompt(schema, errors),
            failure_report={
                "missing_required": [error["path"] for error in errors if error["code"] == "missing_required"],
                "schema_errors": errors,
            },
        )
    if semantic_validator is not None:
        ok, message = semantic_validator(value)
        if not ok:
            error = {"type": "semantic", "path": "", "code": "semantic_validation", "message": message}
            return StructuredOutputRepairResult(
                ok=False,
                value=None,
                repaired=repaired,
                attempts=max(1, attempts),
                errors=[error],
                retry_prompt=_retry_prompt(schema, [error]),
                failure_report={"semantic_error": message},
            )
    return StructuredOutputRepairResult(
        ok=True,
        value=value,
        repaired=repaired,
        attempts=attempts,
        errors=[],
        retry_prompt=_retry_prompt(schema),
        failure_report={},
    )


def _schema_errors(value: dict[str, Any], schema: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    required = list(schema.get("required", []))
    for name in required:
        if name not in value:
            errors.append(
                {
                    "type": "schema",
                    "path": name,
                    "code": "missing_required",
                    "message": f"missing required field: {name}",
                }
            )
    properties = schema.get("properties") or {}
    if schema.get("additionalProperties") is False:
        for name in value:
            if name not in properties:
                errors.append(
                    {
                        "type": "schema",
                        "path": name,
                        "code": "unknown_field",
                        "message": f"unknown field: {name}",
                    }
                )
    for name, spec in properties.items():
        if name not in value:
            continue
        expected = spec.get("type")
        if expected and not _matches_type(value[name], expected):
            errors.append(
                {
                    "type": "schema",
                    "path": name,
                    "code": "type_mismatch",
                    "message": f"{name} must be {expected}",
                }
            )
    return errors


def _matches_type(value: Any, expected: str) -> bool:
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, int | float) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    return True


def _parse_json_object(text: str) -> dict[str, Any]:
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError("structured output must be a JSON object")
    return parsed


def _repair_json_text(raw_text: str) -> str:
    text = _extract_object(raw_text)
    text = re.sub(r",\s*([}\]])", r"\1", text)
    text = _close_brackets(text)
    return text


def _extract_object(text: str) -> str:
    start = text.find("{")
    if start < 0:
        raise ValueError("no JSON object found")
    end = text.rfind("}")
    if end < start:
        return text[start:]
    return text[start : end + 1]


def _close_brackets(text: str) -> str:
    braces = text.count("{") - text.count("}")
    brackets = text.count("[") - text.count("]")
    return text + ("]" * max(0, brackets)) + ("}" * max(0, braces))


def _retry_prompt(schema: dict[str, Any], errors: list[dict[str, Any]] | None = None) -> str:
    lines = [
        "Return only valid JSON matching this schema.",
        json.dumps(schema, ensure_ascii=False, sort_keys=True),
    ]
    if errors:
        lines.append("Errors:")
        lines.extend(f"- {error['path']}: {error['message']}" for error in errors)
    return "\n".join(lines)


__all__ = [
    "StructuredOutputRepairResult",
    "repair_structured_output",
    "validate_or_repair",
]
