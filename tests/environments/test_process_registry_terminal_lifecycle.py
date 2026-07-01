"""Process registry and terminal lifecycle tests (Task 168)."""

from __future__ import annotations

from proseforge_agent.cli import main
from proseforge_agent.environments import FakeProcessBackend, ProcessRegistry


def test_process_registry_tracks_start_read_close(tmp_path):
    registry = ProcessRegistry(root=tmp_path, backend=FakeProcessBackend())

    entry = registry.start(command=["python", "--version"], environment_id="fake")
    read = registry.read(entry.process_id)
    closed = registry.close(entry.process_id)

    assert entry.status == "running"
    assert read.output == "python --version"
    assert closed.status == "closed"
    loaded = ProcessRegistry(root=tmp_path, backend=FakeProcessBackend()).list()
    assert loaded[0].process_id == entry.process_id
    assert loaded[0].status == "closed"


def test_process_registry_interrupt_and_cleanup(tmp_path):
    registry = ProcessRegistry(root=tmp_path, backend=FakeProcessBackend())
    entry = registry.start(command=["sleep", "10"], environment_id="fake")

    interrupted = registry.interrupt(entry.process_id)
    cleaned = registry.cleanup_stale()

    assert interrupted.status == "interrupted"
    assert cleaned == []


def test_process_registry_bounds_and_redacts_output(tmp_path):
    registry = ProcessRegistry(root=tmp_path, backend=FakeProcessBackend(output="token=secret and long output"), output_limit=12)

    entry = registry.start(command=["run"], environment_id="fake")
    read = registry.read(entry.process_id)

    assert read.output == "token=[redac"
    assert read.truncated is True


def test_processes_cli_list(capsys):
    assert main(["processes", "list"]) == 0

    out = capsys.readouterr().out
    assert "Processes" in out
