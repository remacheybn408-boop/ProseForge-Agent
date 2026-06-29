# Task 173: Tool Result Artifacts And Output Limits

## Goal

Add artifact storage and output limits for large tool results across terminal, browser, media, and gateway tools.

## Architecture Notes

Model context should receive concise summaries plus artifact references. Large raw outputs remain in bounded artifact storage with redaction and retention policy.

## Files

- Create `src/proseforge_agent/agent/artifacts.py`.
- Extend tool result handling in `src/proseforge_agent/agent/tools.py`.
- Add tests in `tests/test_tool_result_artifacts_output_limits.py`.

## Interfaces / Contracts

- `ArtifactStore.write(kind, content, metadata) -> ArtifactRef`.
- `ToolResult` includes `summary`, `artifact_refs`, `truncated`, and `redaction_applied`.
- `pf-agent artifacts list`.

## TDD Steps

- [ ] Write failing test `tests/test_tool_result_artifacts_output_limits.py::test_large_tool_result_is_summarized_with_artifact_ref`.
- [ ] Run `python -m pytest tests/test_tool_result_artifacts_output_limits.py::test_large_tool_result_is_summarized_with_artifact_ref -q` and confirm failure.
- [ ] Implement artifact store, output limit policy, redaction, summaries, and CLI listing.
- [ ] Run the targeted test and confirm pass.
- [ ] Add companion tests for binary artifacts, retention cleanup, path containment, support-bundle redaction, and missing artifact refs.
- [ ] Run `python -m pytest tests/test_tool_result_artifacts_output_limits.py -q` and `python -m pytest -q`.
- [ ] Commit with `feat: add tool result artifacts and output limits`.

## Verification

```powershell
python -m pytest tests/test_tool_result_artifacts_output_limits.py -q
pf-agent artifacts list
python -m pytest -q
```

## Acceptance

- Large tool outputs never flood prompt context.
- Artifact refs are portable and path-contained.
- Redaction happens before persistence and display.
- Retention cleanup is deterministic.

## Commit Boundary

Commit only Task 173 artifact, tool result, tests, fixtures, and CLI wiring files. Do not bundle adjacent task cards.

