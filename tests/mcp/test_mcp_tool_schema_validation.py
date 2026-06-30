"""MCP tool schema validation tests (Task 120)."""

from __future__ import annotations

from proseforge_agent.mcp import MCPSchemaCache, MCPSchemaValidator


def test_mcp_tool_schema_validation_normalizes_paths_and_rejects_unknown_fields():
    validator = MCPSchemaValidator(
        input_schema={
            "type": "object",
            "required": ["path"],
            "properties": {"path": {"type": "string"}, "text": {"type": "string"}},
            "additionalProperties": False,
        }
    )

    ok = validator.validate_input({"path": ".\\drafts\\ch_001.md", "text": "hello"})
    unknown = validator.validate_input({"path": "drafts/ch_001.md", "extra": True})
    traversal = validator.validate_input({"path": "../secrets.env"})

    assert ok.valid is True
    assert ok.normalized_payload["path"] == "drafts/ch_001.md"
    assert unknown.valid is False
    assert "unknown field: extra" in unknown.errors
    assert traversal.valid is False
    assert "path escapes workspace: path" in traversal.errors


def test_mcp_tool_schema_validation_checks_required_and_output_schema():
    validator = MCPSchemaValidator(
        input_schema={"required": ["path"]},
        output_schema={
            "type": "object",
            "required": ["content"],
            "properties": {"content": {"type": "string"}},
            "additionalProperties": False,
        },
    )

    missing = validator.validate_input({})
    output_ok = validator.validate_output({"content": "hello"})
    output_bad = validator.validate_output({"content": 7, "extra": "x"})

    assert missing.valid is False
    assert "missing required field: path" in missing.errors
    assert output_ok.valid is True
    assert output_bad.valid is False
    assert "field content must be string" in output_bad.errors
    assert "unknown field: extra" in output_bad.errors


def test_mcp_schema_cache_versions_are_stable(tmp_path):
    cache = MCPSchemaCache(tmp_path)
    first = cache.remember("filesystem", "read_file", {"required": ["path"]})
    second = MCPSchemaCache(tmp_path).remember("filesystem", "read_file", {"required": ["path"]})
    changed = cache.remember("filesystem", "read_file", {"required": ["path", "text"]})

    assert first.version == second.version
    assert changed.version != first.version
    assert cache.get("filesystem", "read_file").version == changed.version
