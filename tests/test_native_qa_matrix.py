import json
from pathlib import Path

from proseforge_agent.cli import main
from proseforge_agent.install.qa_matrix import NativeQAMatrix


FIXTURE = Path(__file__).parent / "fixtures" / "cross-platform-native-qa-matrix" / "expected_matrix.json"


def test_required_matrix_covers_three_native_platforms():
    matrix = NativeQAMatrix.required_checks()
    platforms = {check.platform for check in matrix}
    assert platforms == {"windows", "macos", "linux"}


def test_each_platform_has_core_operator_flows():
    checks = NativeQAMatrix.required_checks()
    by_platform = NativeQAMatrix.group_by_platform(checks)
    for platform in ("windows", "macos", "linux"):
        names = {check.name for check in by_platform[platform]}
        assert {"install", "chat", "doctor", "uninstall"}.issubset(names)


def test_coverage_report_blocks_missing_required_checks():
    report = NativeQAMatrix().validate_coverage({"windows.install", "macos.install"})
    assert report.status == "blocked"
    assert "linux.doctor" in report.missing


def test_matrix_can_render_fixture_shape():
    expected = json.loads(FIXTURE.read_text(encoding="utf-8"))
    payload = NativeQAMatrix().to_dict()
    assert set(payload["platforms"]) == set(expected["platforms"])
    assert payload["platforms"]["windows"][0]["name"] == "install"


def test_qa_matrix_cli(capsys):
    code = main(["qa", "matrix", "--show"])
    out = capsys.readouterr().out
    assert code == 0
    assert "Native QA Matrix" in out


def test_fixture_loads():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert "linux" in payload["platforms"]
