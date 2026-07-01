"""Media generation and transcription managed tool tests (Task 172)."""

from __future__ import annotations

from proseforge_agent.cli import main
from proseforge_agent.tools.managed.media import FakeMediaGateway, MediaRequest


def test_transcription_returns_artifact_and_text_candidate():
    gateway = FakeMediaGateway(provider="fake")

    result = gateway.transcribe(MediaRequest(fixture="voice-note", content_type="audio/wav"))

    assert result.status == "ok"
    assert result.artifact_ref.kind == "transcript"
    assert result.text_candidate == "Transcription candidate for voice-note."
    assert result.accepted_to_canon is False
    assert result.redaction_applied is True


def test_image_generation_dry_run_returns_artifact_metadata_without_canon_write():
    gateway = FakeMediaGateway(provider="fake")

    result = gateway.generate_image("cover concept with secret token=123", dry_run=True)

    assert result.status == "planned"
    assert result.artifact_ref.kind == "image"
    assert result.metadata["dry_run"] is True
    assert "token=123" not in result.metadata["prompt"]
    assert result.accepted_to_canon is False


def test_missing_media_backend_degrades_cleanly():
    gateway = FakeMediaGateway(provider="missing")

    result = gateway.transcribe(MediaRequest(fixture="voice-note", content_type="audio/wav"))

    assert result.status == "degraded"
    assert "not configured" in result.reason


def test_media_cli_transcribe(capsys):
    assert main(["media", "transcribe", "--fixture", "voice-note", "--provider", "fake"]) == 0

    out = capsys.readouterr().out
    assert "Managed Media" in out
    assert "voice-note" in out


def test_media_cli_image_dry_run(capsys):
    assert main(["media", "image", "--prompt", "cover concept", "--provider", "fake", "--dry-run"]) == 0

    out = capsys.readouterr().out
    assert "Managed Media" in out
    assert "planned" in out
