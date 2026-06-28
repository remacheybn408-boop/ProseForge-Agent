import json
from pathlib import Path

from proseforge_agent.cli import main
from proseforge_agent.install.local_models import LocalModelDetector
from proseforge_agent.install.secrets import SecretStore


FIXTURE = Path(__file__).parent / "fixtures" / "offline-local-model-setup" / "models_response.json"


class FakeHttp:
    def __init__(self, payload=None, fail=False):
        self.payload = payload or {"models": [{"name": "llama3"}]}
        self.fail = fail
        self.calls = []

    def get_json(self, url):
        self.calls.append(url)
        if self.fail:
            raise RuntimeError("offline")
        return self.payload


def test_unreachable_endpoint_is_skipped_with_note_not_exception():
    detector = LocalModelDetector(FakeHttp(fail=True))
    candidates = detector.detect(endpoints=["http://127.0.0.1:11434"])
    assert candidates == []
    assert detector.notes


def test_candidate_profile_reuses_openai_compatible_shape():
    candidates = LocalModelDetector(FakeHttp()).detect(endpoints=["http://127.0.0.1:1234"])
    assert candidates[0].privacy == "local"
    assert candidates[0].profile_shape == "openai_compatible"


def test_local_server_token_is_stored_through_secret_store():
    detector = LocalModelDetector(FakeHttp(), secret_store=SecretStore.for_platform("linux", False))
    assert detector.store_token("lmstudio", "local-token") == "secret://lmstudio/api_key"


def test_detection_uses_injected_http_only():
    http = FakeHttp()
    LocalModelDetector(http).detect(endpoints=["http://example.test"])
    assert http.calls == ["http://example.test/v1/models"]


def test_chinese_model_display_names_round_trip():
    candidates = LocalModelDetector(FakeHttp({"models": [{"name": "本地模型"}]})).detect(
        endpoints=["http://127.0.0.1:1234"]
    )
    assert candidates[0].models == ["本地模型"]


def test_provider_discover_local_cli(capsys):
    code = main(["provider", "discover-local"])
    out = capsys.readouterr().out
    assert code == 0
    assert "Local Models" in out


def test_models_response_fixture_loads():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert payload["models"][0]["name"] == "本地模型"
