"""Unified secret redaction across events and trajectories (Task 198)."""

from __future__ import annotations

import json

import pytest

from proseforge_agent.agent.events import _redact
from proseforge_agent.eval.trajectories import _redact_with_text


def test_redact_scans_secret_inside_string_value():
    payload = {"log_line": "Authorization: Bearer sk-super-secret-123"}
    out = _redact(payload)
    dumped = json.dumps(out)
    assert "sk-super-secret-123" not in dumped
    assert "[redacted]" in dumped


def test_redact_scans_assignment_secret_in_string():
    payload = {"cmd": "curl -H token=abc123def456 https://x"}
    out = _redact(payload)
    assert "abc123def456" not in json.dumps(out)


@pytest.mark.parametrize(
    "key",
    ["cookie", "refresh_token", "client_secret", "private_key", "credential", "bearer"],
)
def test_expanded_sensitive_keys_are_redacted_by_key(key):
    out = _redact({key: "leak-me"})
    assert out[key] == "[redacted]"


def test_nested_dict_string_secret_is_redacted():
    payload = {"outer": {"inner": {"note": "key sk-deep-secret-xyz here"}}}
    out = _redact(payload)
    assert "sk-deep-secret-xyz" not in json.dumps(out)


def test_trajectory_nested_text_field_is_redacted():
    payload = {"data": {"text": "MY PRIVATE DRAFT"}}
    out = _redact_with_text(payload, {"text"})
    assert out["data"]["text"] == "[redacted]"


def test_trajectory_list_nested_text_field_is_redacted():
    payload = {"results": [{"text": "SECRET A"}, {"text": "SECRET B"}]}
    out = _redact_with_text(payload, {"text"})
    assert out["results"][0]["text"] == "[redacted]"
    assert out["results"][1]["text"] == "[redacted]"


def test_trajectory_top_level_text_field_still_redacted():
    out = _redact_with_text({"text": "top", "other": "keep"}, {"text"})
    assert out["text"] == "[redacted]"
    assert out["other"] == "keep"


def test_mcp_credentials_redact_sensitive_still_available():
    from proseforge_agent.mcp.credentials import redact_sensitive

    out = redact_sensitive({"log": "Authorization: Bearer sk-abc-123"})
    assert "sk-abc-123" not in json.dumps(out)
