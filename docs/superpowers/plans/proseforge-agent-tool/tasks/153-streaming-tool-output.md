# Task 153: Streaming Tool Output

## Goal

Expose streaming tool output in terminal and gateway-safe form without changing final tool-result semantics.

## Architecture Notes

Streaming is observational. The final stored tool result must match the non-streaming result, while intermediate chunks are delivered through the event bus with size limits and redaction.

## Files

- Extend `src/proseforge_agent/agent/events.py` and `src/proseforge_agent/agent/tools.py`.
- Add `src/proseforge_agent/tui/streaming.py`.
- Add tests in `tests/test_streaming_tool_output.py`.

## Interfaces / Contracts

- `ToolOutputChunk` carries `tool_call_id`, `sequence`, `text`, `is_final`, and redaction metadata.
- Terminal surfaces can subscribe to chunks.
- Gateways can request chunk coalescing by byte or character limit.

## TDD Steps

- [ ] Write failing test `tests/test_streaming_tool_output.py::test_stream_chunks_reconstruct_final_result`.
- [ ] Run `python -m pytest tests/test_streaming_tool_output.py::test_stream_chunks_reconstruct_final_result -q` and confirm failure.
- [ ] Implement chunk events, aggregation, limits, and redaction.
- [ ] Run the targeted test and confirm pass.
- [ ] Add companion tests for cancellation, oversized chunks, binary output, and secret redaction.
- [ ] Run `python -m pytest tests/test_streaming_tool_output.py -q` and `python -m pytest -q`.
- [ ] Commit with `feat: add streaming tool output`.

## Verification

```powershell
python -m pytest tests/test_streaming_tool_output.py -q
pf-agent chat --message "run streaming fake tool" --provider fake --no-project --show-events
python -m pytest -q
```

## Acceptance

- Streaming chunks reconstruct the same final result as non-streaming execution.
- Secret and path redaction applies before display.
- Interruptions close streams cleanly.
- No surface stores unbounded output in memory.

## Commit Boundary

Commit only Task 153 event, streaming, tool, test, fixture, and minimal CLI/TUI wiring files. Do not bundle adjacent task cards.

