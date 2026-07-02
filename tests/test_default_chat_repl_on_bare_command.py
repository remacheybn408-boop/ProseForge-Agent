"""Default chat REPL on bare command tests (Task 186)."""

from __future__ import annotations

from proseforge_agent.cli import main


def test_bare_command_launches_chat_repl_when_provider_is_configured(monkeypatch):
    called = {}

    def fake_run_repl(argv=None, *, provider="fake", **kwargs):
        called["provider"] = provider
        return 0

    monkeypatch.setattr("proseforge_agent.chat.repl.run_repl", fake_run_repl)
    monkeypatch.setattr(
        "proseforge_agent.setup.first_run.FirstRunBootstrap.check",
        lambda self: _ready_verdict(),
    )

    exit_code = main([])

    assert exit_code == 0
    assert called["provider"] == "fake"


def test_bare_command_routes_to_first_run_when_not_configured(monkeypatch, capsys):
    called = {}

    def fake_run_repl(argv=None, *, provider="fake", **kwargs):
        called["ran"] = True
        return 0

    monkeypatch.setattr("proseforge_agent.chat.repl.run_repl", fake_run_repl)
    monkeypatch.setattr(
        "proseforge_agent.setup.first_run.FirstRunBootstrap.check",
        lambda self: _not_ready_verdict(),
    )

    exit_code = main([])

    assert exit_code == 2
    assert "ran" not in called  # REPL must not launch on an unconfigured machine
    out = capsys.readouterr().out
    assert out.strip()  # setup guidance is printed


def test_no_default_flag_prints_help_and_exits_zero(capsys):
    exit_code = main(["--no-default"])

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "pf-agent" in out
    assert "usage" in out.lower()


def test_help_flag_still_prints_help(capsys):
    exit_code = main(["--help"])

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "pf-agent" in out


def test_bare_command_never_prints_python_traceback_on_repl_error(monkeypatch, capsys):
    def boom(argv=None, *, provider="fake", **kwargs):
        raise RuntimeError("repl exploded")

    monkeypatch.setattr("proseforge_agent.chat.repl.run_repl", boom)
    monkeypatch.setattr(
        "proseforge_agent.setup.first_run.FirstRunBootstrap.check",
        lambda self: _ready_verdict(),
    )

    exit_code = main([])

    assert exit_code == 2
    captured = capsys.readouterr()
    combined = captured.out + captured.err
    assert "Traceback" not in combined
    assert "repl exploded" in combined


def test_run_repl_is_importable_and_callable():
    from proseforge_agent.chat import repl

    assert callable(repl.run_repl)


def _ready_verdict():
    from proseforge_agent.setup.first_run import FirstRunVerdict

    return FirstRunVerdict(ready=True, reasons=[])


def _not_ready_verdict():
    from proseforge_agent.setup.first_run import FirstRunVerdict

    return FirstRunVerdict(ready=False, reasons=["config missing"])
