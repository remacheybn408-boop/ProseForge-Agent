"""MCP tool schema validation and version caching."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import PurePosixPath, Path
from typing import Any

from ..errors import ConfigurationError


@dataclass(frozen=True)
class MCPSchemaValidationResult:
    """Structured schema validation result."""

    valid: bool
    normalized_payload: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MCPSchemaVersion:
    """Cached schema version metadata."""

    server_id: str
    tool_name: str
    version: str
    schema: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MCPSchemaValidator:
    """Validate MCP tool payloads against a compact JSON-schema subset."""

    def __init__(
        self,
        *,
        input_schema: dict[str, Any] | None = None,
        output_schema: dict[str, Any] | None = None,
    ) -> None:
        self.input_schema = input_schema or {}
        self.output_schema = output_schema or {}

    def validate_input(self, payload: dict[str, Any]) -> MCPSchemaValidationResult:
        return self._validate(payload, self.input_schema, normalize_paths=True)

    def validate_output(self, payload: dict[str, Any]) -> MCPSchemaValidationResult:
        return self._validate(payload, self.output_schema, normalize_paths=False)

    def _validate(
        self,
        payload: dict[str, Any],
        schema: dict[str, Any],
        *,
        normalize_paths: bool,
    ) -> MCPSchemaValidationResult:
        normalized = dict(payload)
        errors: list[str] = []
        required = list(schema.get("required") or [])
        properties = dict(schema.get("properties") or {})
        for field_name in required:
            if field_name not in payload:
                errors.append(f"missing required field: {field_name}")
        if schema.get("additionalProperties") is False:
            for field_name in sorted(payload):
                if field_name not in properties:
                    errors.append(f"unknown field: {field_name}")
        for field_name, rules in properties.items():
            if field_name not in payload:
                continue
            value = payload[field_name]
            expected_type = rules.get("type") if isinstance(rules, dict) else None
            if expected_type and not _matches_type(value, expected_type):
                errors.append(f"field {field_name} must be {expected_type}")
            if normalize_paths and _looks_like_path_field(field_name):
                path = _normalize_relative_path(str(value))
                if path is None:
                    errors.append(f"path escapes workspace: {field_name}")
                else:
                    normalized[field_name] = path
        return MCPSchemaValidationResult(valid=not errors, normalized_payload=normalized, errors=errors)


class MCPSchemaCache:
    """Persist schema versions by server/tool."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.path = self.root / "mcp" / "schema_cache.json"

    def remember(self, server_id: str, tool_name: str, schema: dict[str, Any]) -> MCPSchemaVersion:
        version = _schema_hash(schema)
        cache = self._read()
        key = f"{server_id}:{tool_name}"
        payload = {
            "server_id": server_id,
            "tool_name": tool_name,
            "version": version,
            "schema": schema,
        }
        cache[key] = payload
        self._write(cache)
        return MCPSchemaVersion(**payload)

    def get(self, server_id: str, tool_name: str) -> MCPSchemaVersion:
        key = f"{server_id}:{tool_name}"
        payload = self._read().get(key)
        if payload is None:
            raise ConfigurationError(f"schema for {key!r} is not cached")
        return MCPSchemaVersion(
            server_id=str(payload["server_id"]),
            tool_name=str(payload["tool_name"]),
            version=str(payload["version"]),
            schema=dict(payload.get("schema") or {}),
        )

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, cache: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _matches_type(value: Any, expected_type: str) -> bool:
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "array":
        return isinstance(value, list)
    return True


def _looks_like_path_field(field_name: str) -> bool:
    lowered = field_name.lower()
    return lowered == "path" or lowered.endswith("_path") or lowered.endswith("path")


def _normalize_relative_path(raw_path: str) -> str | None:
    path = PurePosixPath(raw_path.replace("\\", "/"))
    if path.is_absolute():
        return None
    parts: list[str] = []
    for part in path.parts:
        if part in {"", "."}:
            continue
        if part == "..":
            return None
        parts.append(part)
    return "/".join(parts)


def _schema_hash(schema: dict[str, Any]) -> str:
    payload = json.dumps(schema, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


__all__ = [
    "MCPSchemaCache",
    "MCPSchemaValidationResult",
    "MCPSchemaValidator",
    "MCPSchemaVersion",
]
