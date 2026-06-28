# Task 63: Streaming Responses

## Goal

Add a streaming generation channel to providers and stream tokens incrementally in the chat REPL.

## Agent Product Requirement

Interactive chat should print the model's answer as it arrives, not after a long silent wait.

> Dependency note: execute after the provider layer (Tasks 04–06) and the chat REPL (Task 35). Logical position: 35.5.

## Architecture Notes

`llm.streaming` adds an optional `generate_stream` channel alongside the existing `generate` method. Providers that support streaming yield text chunks; providers that do not fall back to a single-chunk stream wrapping `generate`, so callers never special-case support. The chat REPL (Task 35) consumes the stream and prints incrementally. The aggregated stream must equal the non-streaming result so transcripts and memory extraction are unaffected.

Read before starting:

- ../architecture/02-system-architecture.md (First Release Interfaces: LLMProvider)
- ../architecture/05-model-provider-adapters.md
- 00-task-index.md

## Files

- Create `src/proseforge_agent/llm/streaming.py`
- Modify `src/proseforge_agent/chat/repl.py`
- Create `tests/test_streaming_responses.py`
- Create `tests/fixtures/streaming-responses/chunks.json`

## Interfaces / Contracts

- `StreamingProvider.generate_stream(messages, temperature=0.7) -> Iterator[StreamChunk]`.
- `StreamChunk` fields: `text`, `index`, `done`.
- Aggregating all chunk `text` equals the `text` of the equivalent non-streaming `generate` call.
- A non-streaming provider is adapted to a single terminal chunk (`done=True`) so consumers are uniform.

## Data Flow

1. The REPL requests a streaming generation.
2. The provider (or fallback wrapper) yields chunks in order.
3. The REPL prints each chunk as it arrives.
4. Chunks are accumulated into the full response.
5. The accumulated text is saved to the transcript exactly as the non-streaming path would.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_streaming_responses.py::test_aggregated_stream_equals_full_text`**

```python
def test_aggregated_stream_equals_full_text(fake_streaming_provider):
    chunks = list(fake_streaming_provider.generate_stream(messages=[{"role": "user", "content": "hi"}]))
    assert chunks[-1].done is True
    assert "".join(c.text for c in chunks) == fake_streaming_provider.generate(
        messages=[{"role": "user", "content": "hi"}]
    ).text
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/test_streaming_responses.py::test_aggregated_stream_equals_full_text -q
```

Expected: FAIL because `StreamingProvider` and `StreamChunk` are missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement `generate_stream`, `StreamChunk`, the non-streaming fallback wrapper, and REPL incremental printing.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/test_streaming_responses.py::test_aggregated_stream_equals_full_text -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

```text
test_non_streaming_provider_yields_single_done_chunk
test_repl_prints_chunks_incrementally
test_transcript_saved_text_matches_non_streaming_result
test_stream_interruption_saves_partial_with_marker
test_stream_chunks_round_trip_utf8_chinese_text
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_streaming_responses.py -q
pf-agent chat --message "讲个开头" --provider fake --stream
```

Expected: tests pass and the chat prints output incrementally, ending with the same full text.

- [ ] **Step 7: Record commit boundary**

```powershell
git add src/proseforge_agent/llm/streaming.py src/proseforge_agent/chat/repl.py tests/test_streaming_responses.py tests/fixtures/streaming-responses
git commit -m "feat: add streaming responses"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Cross-Platform Notes

- Chunked output flushes correctly in PowerShell, Bash, Zsh, and Fish.
- UTF-8 chunks never split a multi-byte character mid-write.
- Works identically on Windows, macOS, and Linux terminals.

## Failure Modes To Prove

- A non-streaming provider still works through a single-chunk stream.
- Aggregated stream text equals the non-streaming result.
- An interrupted stream saves the partial response with a marker.
- UTF-8 Chinese text streams without corruption.

## Verification

```powershell
python -m pytest tests/test_streaming_responses.py -q
pf-agent chat --message "讲个开头" --provider fake --stream
```

## Acceptance

- Providers expose an optional streaming channel with a uniform fallback.
- The REPL prints incrementally.
- Streamed and non-streamed transcripts match.
- Streaming is correct for UTF-8 Chinese text.

## Commit Boundary

Commit only streaming files, the REPL change, and tests after verification passes. Do not alter the non-streaming `generate` contract.
