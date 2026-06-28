import json
from pathlib import Path

from proseforge_agent.cli import main
from proseforge_agent.install.windows import WindowsChecks


FIXTURE = Path(__file__).parent / "fixtures" / "windows-native-support" / "env_samples.json"


def test_bare_cmd_without_utf8_warns_with_ascii_fallback():
    checks = WindowsChecks({"COMSPEC": "cmd.exe", "PYTHONUTF8": "0"}).run()
    utf8 = next(check for check in checks if check.name == "powershell_utf8")
    assert utf8.status == "warn"
    assert "ASCII" in utf8.detail


def test_credential_manager_unavailable_recommends_env_fallback():
    checks = WindowsChecks({"CREDENTIAL_MANAGER": "0"}).run()
    cred = next(check for check in checks if check.name == "credential_manager")
    assert cred.status == "warn"
    assert cred.recovery


def test_long_path_check_flags_disabled_long_paths():
    checks = WindowsChecks({"LONG_PATHS_ENABLED": "0"}).run()
    long_paths = next(check for check in checks if check.name == "long_paths")
    assert long_paths.status == "warn"
    assert "LongPathsEnabled" in long_paths.recovery


def test_path_with_spaces_is_handled_as_normal():
    checks = WindowsChecks({"APPDATA": "C:/Users/A B/Roaming", "LOCALAPPDATA": "C:/Users/A B/Local"}).run()
    spaces = next(check for check in checks if check.name == "spaces_in_paths")
    assert spaces.status == "ok"


def test_chinese_project_path_round_trips():
    checks = WindowsChecks({"APPDATA": "C:/用户/作者/Roaming", "LOCALAPPDATA": "C:/用户/作者/Local"}).run()
    assert any("作者" in check.detail for check in checks)


def test_windows_doctor_cli(capsys):
    code = main(["doctor", "--section", "windows"])
    out = capsys.readouterr().out
    assert code == 0
    assert "powershell_utf8" in out


def test_windows_fixture_loads():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert payload["windows_terminal"]["WT_SESSION"] == "abc"
