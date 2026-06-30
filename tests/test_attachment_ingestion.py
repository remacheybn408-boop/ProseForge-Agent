"""Attachment ingestion tests (Task 114)."""

from __future__ import annotations

import json

from proseforge_agent.agent.attachments import AttachmentIngestor
from proseforge_agent.cli import main


PNG_1X1 = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR"
    b"\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00"
    b"\x90wS\xde"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


def test_attachment_ingestion_writes_searchable_artifact_and_memory_candidate(tmp_path):
    source = tmp_path / "notes.md"
    source.write_text("# Research\nThe map shows a hidden harbor.\n", encoding="utf-8")

    result = AttachmentIngestor(tmp_path).ingest_file(source, slug="demo_novel")

    assert result.status == "ok"
    assert result.kind == "markdown"
    assert result.searchable_path is not None
    assert "hidden harbor" in result.searchable_path.read_text(encoding="utf-8")
    assert result.artifact_path.exists()
    assert result.memory_candidate_path is not None
    candidate = json.loads(result.memory_candidate_path.read_text(encoding="utf-8").splitlines()[0])
    assert candidate["project_slug"] == "demo_novel"
    assert candidate["source"].endswith("notes.md")


def test_attachment_ingestion_extracts_csv_and_image_metadata(tmp_path):
    csv_path = tmp_path / "cast.csv"
    csv_path.write_text("name,role\nAda,cartographer\n", encoding="utf-8")
    image_path = tmp_path / "map.png"
    image_path.write_bytes(PNG_1X1)

    ingestor = AttachmentIngestor(tmp_path, vision_describer=lambda path: f"vision:{path.name}")
    csv_result = ingestor.ingest_file(csv_path, slug="demo_novel")
    image_result = ingestor.ingest_image(image_path, slug="demo_novel")

    assert "Ada" in csv_result.text
    assert image_result.metadata["format"] == "png"
    assert image_result.metadata["width"] == 1
    assert image_result.metadata["height"] == 1
    assert image_result.text == "vision:map.png"


def test_attachment_ingestion_folder_sorts_supported_files(tmp_path):
    folder = tmp_path / "research"
    folder.mkdir()
    (folder / "b.txt").write_text("second", encoding="utf-8")
    (folder / "a.txt").write_text("first", encoding="utf-8")
    (folder / "skip.bin").write_bytes(b"\x00")

    results = AttachmentIngestor(tmp_path).ingest_folder(folder, slug="demo_novel")

    assert [result.source_path.name for result in results] == ["a.txt", "b.txt"]


def test_attachment_ingestion_cli_file_image_folder(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    note = tmp_path / "note.txt"
    note.write_text("plain note", encoding="utf-8")
    image = tmp_path / "map.png"
    image.write_bytes(PNG_1X1)
    folder = tmp_path / "research"
    folder.mkdir()
    (folder / "data.csv").write_text("key,value\nx,1\n", encoding="utf-8")

    assert main(["ingest", "file", str(note), "--slug", "demo_novel"]) == 0
    assert main(["ingest", "image", str(image), "--slug", "demo_novel"]) == 0
    assert main(["ingest", "folder", str(folder), "--slug", "demo_novel"]) == 0

    out = capsys.readouterr().out
    assert "Attachment Ingestion" in out
    assert "demo_novel" in out
