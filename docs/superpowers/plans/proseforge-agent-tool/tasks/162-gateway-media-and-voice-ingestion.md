# Task 162: Gateway Media And Voice Ingestion

## Goal

Add gateway-safe media and voice ingestion for attachments, images, documents, and voice notes.

## Architecture Notes

Media ingestion creates bounded attachment records and optional transcription/vision jobs. It does not dump large binary blobs into chat transcripts or model prompts directly.

## Files

- Create `src/proseforge_agent/gateway/media.py`.
- Extend `src/proseforge_agent/chat/retrieval.py` or attachment ingestion from Task 114 when present.
- Add tests in `tests/gateway/test_gateway_media_voice_ingestion.py`.

## Interfaces / Contracts

- `MediaIngestion.ingest(event_attachment) -> AttachmentRecord`.
- `pf-agent gateway media inspect --fixture <name>`.
- Voice transcription and vision extraction are optional provider/tool capabilities with deterministic fake implementations.

## TDD Steps

- [ ] Write failing test `tests/gateway/test_gateway_media_voice_ingestion.py::test_voice_note_creates_transcription_candidate`.
- [ ] Run `python -m pytest tests/gateway/test_gateway_media_voice_ingestion.py::test_voice_note_creates_transcription_candidate -q` and confirm failure.
- [ ] Implement attachment records, size checks, content hashing, fake transcription, and degraded mode.
- [ ] Run the targeted test and confirm pass.
- [ ] Add companion tests for oversized files, unknown media types, image metadata, document text extraction, and redaction.
- [ ] Run `python -m pytest tests/gateway/test_gateway_media_voice_ingestion.py -q` and `python -m pytest -q`.
- [ ] Commit with `feat: add gateway media and voice ingestion`.

## Verification

```powershell
python -m pytest tests/gateway/test_gateway_media_voice_ingestion.py -q
pf-agent gateway media inspect --fixture voice-note --provider fake
python -m pytest -q
```

## Acceptance

- Attachments become bounded, content-addressed records.
- Voice notes can produce transcription candidates through a fake provider path.
- Missing media dependencies degrade without crashing chat.
- No raw large binary data is injected into prompts.

## Commit Boundary

Commit only Task 162 gateway media files, tests, fixtures, and minimal wiring. Do not bundle adjacent task cards.

