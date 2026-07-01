"""Streaming tool output tests (Task 153)."""

from __future__ import annotations

import json

from proseforge_agent.agent.events import EventBus, ToolOutputChunk
from proseforge_agent.cli import main
from proseforge_agent.tui.streaming import ToolOutputStreamer, coalesce_chunks


def test_stream_chunks_reconstruct_final_result(tmp_path):
    event_bus = EventBus(tmp_path / "events.jsonl")
    streamer = ToolOutputStreamer(tool_call_id="call_1", event_bus=event_bus, chunk_char_limit=6)

    chunks = streamer.stream_text("alpha beta gamma")

    assert coalesce_chunks(chunks) == "alpha beta gamma"
    assert chunks[-1].is_final is True
    assert all(len(chunk.text) <= 6 for chunk in chunks)
    records = [json.loads(line) for line in (tmp_path / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    assert records[0]["event_type"] == "tool.output.chunk"


def test_stream_redacts_secret_text_before_display():
    chunks = ToolOutputStreamer(tool_call_id="call_1").stream_text("token=abc123")

    assert coalesce_chunks(chunks) == "token=[redacted]"
    assert chunks[0].redacted is True


def test_stream_binary_output_is_bounded_placeholder():
    chunks = ToolOutputStreamer(tool_call_id="call_1").stream_binary(b"\x00\x01\x02")

    assert coalesce_chunks(chunks) == "[binary output: 3 bytes]"


def test_cancelled_stream_closes_cleanly():
    chunk = ToolOutputStreamer(tool_call_id="call_1").cancel()

    assert isinstance(chunk, ToolOutputChunk)
    assert chunk.is_final is True
    assert chunk.cancelled is True


def test_chat_cli_show_events_smoke(capsys):
    assert main(["chat", "--message", "run streaming fake tool", "--provider", "fake", "--no-project", "--show-events"]) == 0

    out = capsys.readouterr().out
    assert "Tool Output Events" in out
    assert "tool_call_id=call_fake" in out
