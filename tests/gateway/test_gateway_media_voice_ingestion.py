"""Gateway media and voice ingestion tests (Task 162)."""

from __future__ import annotations

from proseforge_agent.cli import main
from proseforge_agent.gateway import MediaIngestion


def test_voice_note_creates_transcription_candidate():
    ingestion = MediaIngestion(provider="fake", max_bytes=1024)

    record = ingestion.ingest(
        {
            "type": "voice",
            "filename": "note.ogg",
            "content": b"voice bytes",
            "mime_type": "audio/ogg",
        }
    )

    assert record.kind == "voice"
    assert record.status == "ok"
    assert record.content_hash
    assert record.transcription_candidate == "fake transcription for note.ogg"
    assert record.content_ref.startswith("sha256:")
    assert record.raw_content is None


def test_media_ingestion_records_image_and_document_metadata():
    ingestion = MediaIngestion(provider="fake", max_bytes=1024)

    image = ingestion.ingest({"type": "image", "filename": "cover.png", "content": b"png", "width": 640, "height": 480})
    document = ingestion.ingest({"type": "document", "filename": "brief.pdf", "content": b"pdf", "mime_type": "application/pdf"})

    assert image.metadata["width"] == 640
    assert image.metadata["height"] == 480
    assert document.metadata["mime_type"] == "application/pdf"


def test_media_ingestion_degrades_oversized_unknown_media():
    record = MediaIngestion(provider="fake", max_bytes=4).ingest(
        {"type": "unknown", "filename": "blob.bin", "content": b"too large"}
    )

    assert record.status == "degraded"
    assert "exceeds" in record.reason


def test_gateway_media_cli_inspect_voice_fixture(capsys):
    assert main(["gateway", "media", "inspect", "--fixture", "voice-note", "--provider", "fake"]) == 0

    out = capsys.readouterr().out
    assert "Gateway Media" in out
    assert "fake transcription" in out
