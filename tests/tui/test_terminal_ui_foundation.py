"""Terminal UI foundation tests (Task 151)."""

from __future__ import annotations

from io import StringIO

from proseforge_agent.cli import main
from proseforge_agent.tui import TerminalApp


def test_terminal_app_renders_initial_state():
    output = StringIO()
    app = TerminalApp(
        provider="fake",
        project=None,
        mode="general_chat",
        input_stream=StringIO("/exit\n"),
        output_stream=output,
    )

    assert app.start() == 0

    rendered = output.getvalue()
    assert "ProseForge Agent TUI" in rendered
    assert "Provider: fake" in rendered
    assert "Project: (none)" in rendered
    assert "Mode: general_chat" in rendered
    assert "Status: running" in rendered


def test_terminal_app_handles_project_and_eof():
    output = StringIO()
    app = TerminalApp(
        provider="fake",
        project="demo",
        mode="project_chat",
        input_stream=StringIO(""),
        output_stream=output,
    )

    assert app.start() == 0
    assert "Project: demo" in output.getvalue()


def test_tui_cli_check_mode(capsys):
    assert main(["tui", "--provider", "fake", "--no-project", "--check"]) == 0

    out = capsys.readouterr().out
    assert "Terminal UI" in out
    assert "provider=fake" in out
