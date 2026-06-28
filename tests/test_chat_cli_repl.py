from io import StringIO
from pathlib import Path
import sys

from proseforge_agent.chat.session import ChatSessionStore
from proseforge_agent.chat.repl import ChatRepl
from proseforge_agent.cli import main
from proseforge_agent.llm import FakeProvider


def test_chat_one_shot_persists_transcript(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    code = main(["chat", "--message", "hello", "--provider", "fake"])
    out = capsys.readouterr().out
    assert code == 0
    assert "Agent Chat" in out
    context = ChatSessionStore(tmp_path / ".pf-agent").load_context("cli")
    assert [message.role for message in context.messages] == ["user", "assistant"]
    assert context.messages[0].content == "hello"


def test_repl_runs_turn_and_exits_on_slash_exit(tmp_path):
    output = StringIO()
    repl = ChatRepl(
        provider=FakeProvider(name="fake", model="fake"),
        session_store=ChatSessionStore(tmp_path),
        input_stream=StringIO("hello\n/exit\n"),
        output_stream=output,
    )
    assert repl.run() == 0
    assert "[fake:fake]" in output.getvalue()
    context = ChatSessionStore(tmp_path).load_context("cli")
    assert context.messages[0].content == "hello"


def test_repl_supports_help_mode_project_and_sessions(tmp_path):
    output = StringIO()
    repl = ChatRepl(
        provider=FakeProvider(name="fake", model="fake"),
        session_store=ChatSessionStore(tmp_path),
        input_stream=StringIO("/help\n/mode project_chat\n/project demo\n/sessions\n/exit\n"),
        output_stream=output,
    )
    assert repl.run() == 0
    text = output.getvalue()
    assert "/mode" in text
    assert "mode: project_chat" in text
    assert "project: demo" in text
    assert "Sessions" in text


def test_repl_eof_exits_zero_without_planned_report(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "stdin", StringIO(""))
    code = main(["chat"])
    out = capsys.readouterr().out
    assert code == 0
    assert "chat (planned)" not in out
    assert (tmp_path / ".pf-agent" / "chats" / "cli" / "session.json").exists()


def test_repl_fixture_is_portable_utf8():
    fixture = Path(__file__).parent / "fixtures" / "chat" / "repl_inputs.txt"
    assert "/mode project_chat" in fixture.read_text(encoding="utf-8")
