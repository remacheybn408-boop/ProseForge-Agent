import json
from pathlib import Path

from proseforge_agent.install.platform_io import (
    ShellCommandRenderer,
    TerminalCaps,
    read_text_utf8,
    write_text_utf8,
)


FIXTURE = Path(__file__).parent / "fixtures" / "cross-platform-path-encoding-terminal" / "paths.json"


def test_bash_renderer_quotes_paths_with_spaces():
    rendered = ShellCommandRenderer("bash").render(["pf-agent", "init", "--out", "my path/file.txt"])
    assert "'my path/file.txt'" in rendered


def test_cmd_falls_back_to_ascii_when_terminal_lacks_utf8():
    caps = TerminalCaps.detect({"COMSPEC": "cmd.exe", "PYTHONUTF8": "0", "WT_SESSION": ""})
    assert caps.supports_utf8 is False
    assert caps.ascii_fallback is True


def test_write_then_read_round_trips_chinese_filename_content(tmp_path):
    path = tmp_path / "章节一.txt"
    write_text_utf8(path, "今天写什么？")
    assert read_text_utf8(path) == "今天写什么？"


def test_terminal_caps_detect_reports_utf8_for_windows_terminal():
    caps = TerminalCaps.detect({"WT_SESSION": "abc", "PYTHONUTF8": "0"})
    assert caps.supports_utf8 is True
    assert caps.ascii_fallback is False


def test_argv_with_special_chars_is_never_left_unquoted():
    rendered = ShellCommandRenderer("powershell").render(["pf-agent", "chat", "--message", "a&b c"])
    assert "'a&b c'" in rendered


def test_paths_fixture_is_utf8_json():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert payload["sample"] == "D:/小说 项目/章节一.txt"
