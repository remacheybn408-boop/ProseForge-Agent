import json
from pathlib import Path

from proseforge_agent.cli import main
from proseforge_agent.install.package_checks import PackageChecker


FIXTURE = Path(__file__).parent / "fixtures" / "pip-pipx-source-installation" / "metadata_sample.json"


def test_package_imports_under_src_layout():
    report = PackageChecker(Path("pyproject.toml")).verify()
    assert next(check for check in report.checks if check.name == "import").status == "ok"


def test_declared_dependencies_resolve():
    report = PackageChecker(Path("pyproject.toml")).verify()
    deps = next(check for check in report.checks if check.name == "dependencies")
    assert deps.status == "ok"
    assert "pyyaml" in deps.detail.lower()


def test_python_version_meets_minimum():
    report = PackageChecker(Path("pyproject.toml")).verify()
    assert next(check for check in report.checks if check.name == "python_version").status == "ok"


def test_packaging_report_lists_failed_checks_with_recovery(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[project]\nrequires-python='>=3.99'\n[project.scripts]\n", encoding="utf-8")
    report = PackageChecker(pyproject).verify()
    failed = [check for check in report.checks if check.status == "fail"]
    assert failed
    assert all(check.recovery for check in failed)


def test_report_paths_are_portable():
    report = PackageChecker(Path("pyproject.toml")).verify()
    assert "\\" not in report.to_dict()["source"]


def test_console_scripts_include_pf_agent():
    assert PackageChecker(Path("pyproject.toml")).console_scripts()["pf-agent"] == "proseforge_agent.cli:main"


def test_metadata_fixture_loads():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert payload["scripts"]["pf-agent"] == "proseforge_agent.cli:main"


def test_doctor_packaging_cli(capsys):
    code = main(["doctor", "--section", "packaging"])
    out = capsys.readouterr().out
    assert code == 0
    assert "packaging" in out
