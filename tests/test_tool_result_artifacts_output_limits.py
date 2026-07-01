"""Tool result artifact and output limit tests (Task 173)."""

from __future__ import annotations

from proseforge_agent.agent.artifacts import ArtifactStore, summarize_tool_output
from proseforge_agent.agent.tools import ToolResult
from proseforge_agent.cli import main


def test_large_tool_result_is_summarized_with_artifact_ref(tmp_path):
    store = ArtifactStore(tmp_path, output_limit=20)

    result = summarize_tool_output("x" * 80, store=store, kind="terminal")

    assert result.summary == "x" * 20
    assert result.truncated is True
    assert result.redaction_applied is False
    assert result.artifact_refs[0].kind == "terminal"
    assert store.read(result.artifact_refs[0].id) == "x" * 80


def test_artifact_store_redacts_before_persistence(tmp_path):
    store = ArtifactStore(tmp_path, output_limit=100)

    ref = store.write("log", "token=secret-value", {"source": "test"})

    assert store.read(ref.id) == "token=[redacted]"
    assert ref.redaction_applied is True


def test_binary_artifact_is_addressed_and_bounded(tmp_path):
    store = ArtifactStore(tmp_path)

    ref = store.write("screenshot", b"\x89PNG data", {"content_type": "image/png"})

    assert ref.kind == "screenshot"
    assert ref.content_type == "image/png"
    assert ref.size_bytes == 9


def test_tool_result_keeps_existing_constructor_compatible():
    result = ToolResult(ok=True, output="hello")

    assert result.summary == ""
    assert result.artifact_refs == []
    assert result.truncated is False


def test_tool_artifacts_cli_list(capsys):
    assert main(["artifacts", "list"]) == 0

    out = capsys.readouterr().out
    assert "Tool Artifacts" in out
