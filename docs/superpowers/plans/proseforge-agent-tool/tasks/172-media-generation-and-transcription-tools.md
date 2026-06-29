# Task 172: Media Generation And Transcription Tools

## Goal

Add optional managed tools for image generation, vision extraction, text-to-speech, and transcription.

## Architecture Notes

Media tools produce artifact records and metadata. They do not write into project canon or manuscripts unless a later workflow explicitly accepts the artifact.

## Files

- Create `src/proseforge_agent/tools/managed/media.py`.
- Add tests in `tests/tools/test_media_generation_transcription_tools.py`.
- Add fixtures under `tests/tools/fixtures/media-tools/`.

## Interfaces / Contracts

- `pf-agent media transcribe --fixture voice-note --provider fake`
- `pf-agent media image --prompt "cover concept" --provider fake --dry-run`
- Media results include artifact ref, content type, prompt/ref metadata, cost hints, and redaction.

## TDD Steps

- [ ] Write failing test `tests/tools/test_media_generation_transcription_tools.py::test_transcription_returns_artifact_and_text_candidate`.
- [ ] Run `python -m pytest tests/tools/test_media_generation_transcription_tools.py::test_transcription_returns_artifact_and_text_candidate -q` and confirm failure.
- [ ] Implement fake media gateway, artifact records, metadata, and dry-run CLI.
- [ ] Run the targeted test and confirm pass.
- [ ] Add companion tests for missing backend, oversized input, unsafe prompt metadata, provider cost hints, and no-canon-write behavior.
- [ ] Run `python -m pytest tests/tools/test_media_generation_transcription_tools.py -q` and `python -m pytest -q`.
- [ ] Commit with `feat: add media generation and transcription tools`.

## Verification

```powershell
python -m pytest tests/tools/test_media_generation_transcription_tools.py -q
pf-agent media transcribe --fixture voice-note --provider fake
python -m pytest -q
```

## Acceptance

- Media tools are optional and fake-testable.
- Artifacts are bounded and content-addressed.
- Generated media is never accepted into project output automatically.
- Missing dependencies produce actionable degraded status.

## Commit Boundary

Commit only Task 172 media tool files, tests, fixtures, and CLI wiring. Do not bundle adjacent task cards.

