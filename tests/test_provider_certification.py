from pathlib import Path

import pytest

from proseforge_agent.cli import main
from proseforge_agent.errors import ConfigurationError
from proseforge_agent.llm.certification import (
    CertificationStore,
    ProviderCertificationRecord,
    ProviderReleaseCheck,
)
from proseforge_agent.llm.docs_refresh import docs_refresh_report, source_urls_for_family


def test_release_check_fails_when_requested_provider_has_no_shape_certification(tmp_path):
    records = CertificationStore(tmp_path)
    records.write(
        provider="openai",
        shape_status="passed",
        source_urls=["https://example.test/openai"],
        checked_date="2026-06-27",
    )
    result = ProviderReleaseCheck(records).run(required=["openai", "deepseek"])
    assert result.status == "failed"
    assert "deepseek" in result.missing_providers


def test_certification_store_round_trips_full_record(tmp_path):
    records = CertificationStore(tmp_path)
    record = records.write(
        provider="openai_main",
        family="openai",
        protocol="openai_chat",
        model="gpt-4o-mini",
        source_urls=["https://example.test/openai"],
        checked_date="2026-06-27",
        shape_status="passed",
        smoke_status="skipped",
        workflow_status="unverified",
        capability_status={"text": "supported"},
        limitations=["vision unverified"],
        next_refresh_due="2026-07-27",
    )
    loaded = records.load("openai_main")
    assert loaded == record
    assert isinstance(loaded, ProviderCertificationRecord)
    assert loaded.next_refresh_due == "2026-07-27"


def test_certification_rejects_non_http_source_url(tmp_path):
    records = CertificationStore(tmp_path)
    with pytest.raises(ConfigurationError):
        records.write(
            provider="openai",
            shape_status="passed",
            source_urls=["not-a-url"],
            checked_date="2026-06-27",
        )


def test_release_check_fails_for_failed_shape_status(tmp_path):
    records = CertificationStore(tmp_path)
    records.write(
        provider="openai",
        shape_status="failed",
        source_urls=["https://example.test/openai"],
        checked_date="2026-06-27",
    )
    result = ProviderReleaseCheck(records).run(required=["openai"])
    assert result.status == "failed"
    assert "openai" in result.failed_providers


def test_docs_refresh_report_uses_official_source_notes():
    urls = source_urls_for_family("openai")
    report = docs_refresh_report(["openai"])
    assert urls
    assert urls[0].startswith("https://")
    assert report.status == "ok"
    assert "openai" in report.data["providers"]


def test_provider_certify_cli_writes_report(tmp_path):
    code = main(
        [
            "provider",
            "certify",
            "--all",
            "--shape-only",
            "--write-report",
            "--out",
            str(tmp_path),
        ]
    )
    assert code == 0
    assert list(Path(tmp_path).glob("provider-certification*"))
