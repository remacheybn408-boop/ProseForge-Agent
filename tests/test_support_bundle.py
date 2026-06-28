import copy
import json
from pathlib import Path

from proseforge_agent.agent import EventBus
from proseforge_agent.cli import main
from proseforge_agent.install.doctor import DoctorCheck, DoctorReport
from proseforge_agent.install.support_bundle import SupportBundleBuilder


FIXTURE = Path(__file__).parent / "fixtures" / "operator-diagnostics-and-support-bundle" / "sample_sources.json"


class DoctorStub:
    def run(self):
        return DoctorReport(
            [
                DoctorCheck(
                    "config",
                    "config",
                    "ok",
                    "path=C:/Users/bijin/.pf-agent/config.yaml api_key=sk-secret",
                )
            ]
        )


def test_support_bundle_writes_redacted_json_files(tmp_path):
    events_path = tmp_path / "events.jsonl"
    EventBus(events_path).emit("provider.status", {"api_key": "secret-value", "path": str(tmp_path)})
    bundle = SupportBundleBuilder(tmp_path, doctor=DoctorStub(), event_log=events_path).build(redact=True)
    payload = json.loads((bundle.path / "support-bundle.json").read_text(encoding="utf-8"))
    serialized = json.dumps(payload, ensure_ascii=False)
    assert bundle.redacted is True
    assert "[redacted]" in serialized
    assert "secret-value" not in serialized
    assert str(tmp_path) not in serialized


def test_support_bundle_does_not_mutate_source_payload(tmp_path):
    source = json.loads(FIXTURE.read_text(encoding="utf-8"))
    original = copy.deepcopy(source)
    SupportBundleBuilder(tmp_path, doctor=DoctorStub()).build(redact=True, sources=source)
    assert source == original


def test_support_bundle_contains_operator_sections(tmp_path):
    bundle = SupportBundleBuilder(tmp_path, doctor=DoctorStub()).build(redact=True)
    assert set(bundle.files) >= {"support-bundle.json", "doctor.json", "events.jsonl"}
    assert bundle.summary["doctor_status"] == "ok"


def test_support_bundle_cli(capsys):
    code = main(["support", "bundle", "--redact"])
    out = capsys.readouterr().out
    assert code == 0
    assert "Support Bundle" in out


def test_support_fixture_loads():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert payload["provider"]["api_key"] == "sk-secret"
