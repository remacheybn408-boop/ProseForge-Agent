import json
from pathlib import Path

from proseforge_agent.cli import main
from proseforge_agent.install.macos import MacOSChecks


FIXTURE = Path(__file__).parent / "fixtures" / "macos-native-support" / "env_samples.json"


def test_keychain_unavailable_recommends_env_fallback():
    checks = MacOSChecks({"HOME": "/Users/alice", "KEYCHAIN_AVAILABLE": "0"}).run()
    keychain = next(check for check in checks if check.name == "keychain")
    assert keychain.status == "warn"
    assert keychain.recovery


def test_application_support_path_uses_library():
    checks = MacOSChecks({"HOME": "/Users/alice"}).run()
    app_support = next(check for check in checks if check.name == "application_support")
    assert "Library/Application Support/ProseForge Agent" in app_support.detail


def test_zsh_shell_reports_ok():
    checks = MacOSChecks({"HOME": "/Users/alice", "SHELL": "/bin/zsh"}).run()
    zsh = next(check for check in checks if check.name == "zsh_shell")
    assert zsh.status == "ok"


def test_gatekeeper_note_is_manual_warning():
    checks = MacOSChecks({"HOME": "/Users/alice"}).run()
    gatekeeper = next(check for check in checks if check.name == "gatekeeper_note")
    assert gatekeeper.status == "warn"
    assert "manual" in gatekeeper.detail.lower()


def test_macos_doctor_cli(capsys):
    code = main(["doctor", "--section", "macos"])
    out = capsys.readouterr().out
    assert code == 0
    assert "keychain" in out


def test_macos_fixture_loads():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert payload["zsh"]["SHELL"] == "/bin/zsh"
