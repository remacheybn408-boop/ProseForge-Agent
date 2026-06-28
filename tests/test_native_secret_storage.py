import json
from pathlib import Path

from proseforge_agent.install.doctor import InstallationDoctor
from proseforge_agent.install.secrets import SecretLookup, SecretStore


FIXTURE = Path(__file__).parent / "fixtures" / "native-secret-storage" / "backends.json"


def test_native_backend_lookup_is_marked_protected():
    lookup = SecretStore.for_platform("windows", backend_available=True).get(
        "OPENAI_API_KEY",
        env={"OPENAI_API_KEY": "sk-secret"},
    )
    assert lookup.backend == "credential_manager"
    assert lookup.protected is True
    assert lookup.value == "sk-secret"


def test_secret_value_never_appears_in_repr_or_report():
    lookup = SecretLookup(value="sk-secret", backend="env_fallback", protected=False, warning="fallback")
    assert "sk-secret" not in repr(lookup)
    report = SecretStore.for_platform("linux", backend_available=False).report_lookup(lookup)
    assert "sk-secret" not in report
    assert "[redacted]" in report


def test_missing_key_returns_lookup_with_none_value_and_recovery():
    lookup = SecretStore.for_platform("linux", backend_available=False).get("MISSING", env={})
    assert lookup.value is None
    assert lookup.backend == "env_fallback"
    assert lookup.warning


def test_doctor_secrets_section_reports_backend_in_use():
    report = InstallationDoctor({"SECRET_BACKEND": "credential_manager"}).run(section="secrets")
    assert report.checks[0].status == "ok"
    assert "credential_manager" in report.checks[0].detail


def test_secret_keys_support_utf8_project_scoped_names():
    key = SecretStore.project_key("demo", "模型")
    assert key == "PROSEFORGE_DEMO_模型_API_KEY"


def test_backends_fixture_loads():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert payload["windows"] == "credential_manager"
