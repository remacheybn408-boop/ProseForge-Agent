import json
from pathlib import Path

from proseforge_agent.cli import main
from proseforge_agent.install.linux import LinuxChecks


FIXTURE = Path(__file__).parent / "fixtures" / "linux-native-support" / "env_samples.json"


def test_xdg_dirs_reports_ok_when_config_home_set():
    checks = LinuxChecks({"HOME": "/home/alice", "XDG_CONFIG_HOME": "/cfg"}).run()
    xdg = next(check for check in checks if check.name == "xdg_dirs")
    assert xdg.status == "ok"
    assert "/cfg/proseforge-agent" in xdg.detail


def test_secret_service_unavailable_warns_with_env_fallback():
    checks = LinuxChecks({"HOME": "/home/alice", "SECRET_SERVICE": "0"}).run()
    secret = next(check for check in checks if check.name == "secret_service")
    assert secret.status == "warn"
    assert "env_fallback" in secret.detail


def test_terminal_utf8_reports_ok_for_utf8_env():
    checks = LinuxChecks({"HOME": "/home/alice", "LANG": "zh_CN.UTF-8"}).run()
    terminal = next(check for check in checks if check.name == "terminal_utf8")
    assert terminal.status == "ok"


def test_systemd_user_service_reports_manual_note():
    checks = LinuxChecks({"HOME": "/home/alice", "SYSTEMD_USER": "0"}).run()
    systemd = next(check for check in checks if check.name == "systemd_user_service")
    assert systemd.status == "warn"
    assert systemd.recovery


def test_linux_doctor_cli(capsys):
    code = main(["doctor", "--section", "linux"])
    out = capsys.readouterr().out
    assert code == 0
    assert "xdg_dirs" in out


def test_linux_fixture_loads():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert payload["xdg"]["XDG_CONFIG_HOME"] == "/cfg"
