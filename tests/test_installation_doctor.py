import json
from pathlib import Path

from proseforge_agent.cli import main
from proseforge_agent.install.doctor import DoctorCheck, DoctorReport, InstallationDoctor


FIXTURE = Path(__file__).parent / "fixtures" / "installation-doctor" / "sample_env.json"


def test_every_failing_check_has_a_recovery_command():
    env = json.loads(FIXTURE.read_text(encoding="utf-8"))
    report = InstallationDoctor(env).run()
    failed = [check for check in report.checks if check.status == "fail"]
    assert failed
    assert all(check.recovery for check in failed)


def test_doctor_section_filter_runs_only_that_group():
    report = InstallationDoctor({"PYTHON_VERSION": "3.11.0"}).run(section="python")
    assert {check.section for check in report.checks} == {"python"}


def test_doctor_does_not_mutate_config_or_secrets():
    env = {"OPENAI_API_KEY": "sk-secret", "PYTHON_VERSION": "3.11.0"}
    before = dict(env)
    report = InstallationDoctor(env).run()
    assert env == before
    assert "sk-secret" not in report.render_markdown()


def test_doctor_report_renders_markdown_and_json():
    report = InstallationDoctor({"PYTHON_VERSION": "3.11.0"}).run(section="python")
    assert isinstance(report, DoctorReport)
    assert "Installation Doctor" in report.render_markdown()
    payload = report.to_dict()
    assert payload["checks"][0]["name"] == "python_version"


def test_doctor_check_dataclass_has_recovery_field():
    check = DoctorCheck(name="x", section="python", status="fail", detail="bad", recovery="fix")
    assert check.recovery == "fix"


def test_doctor_cli_runs(capsys):
    code = main(["doctor"])
    out = capsys.readouterr().out
    assert code == 0
    assert "Installation Doctor" in out
