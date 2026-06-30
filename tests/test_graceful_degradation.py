"""Graceful degradation tests (Task 124)."""

from __future__ import annotations

from proseforge_agent.agent.degradation import CapabilityRuntime, FeatureLevel


def test_graceful_degradation_reports_available_and_degraded_features():
    runtime = CapabilityRuntime(available_level=FeatureLevel.OFFLINE, dependencies={"provider": False})

    export = runtime.check("export_txt")
    rewrite = runtime.check("rewrite")
    report = runtime.report()

    assert export.allowed is True
    assert rewrite.allowed is False
    assert rewrite.status == "degraded"
    assert "requires provider" in rewrite.guidance
    assert report.available_level == "offline"
    assert report.features["export_txt"]["status"] == "ok"
    assert report.features["rewrite"]["status"] == "degraded"


def test_graceful_degradation_allows_features_at_or_below_level():
    offline = CapabilityRuntime(available_level=FeatureLevel.OFFLINE)
    local = CapabilityRuntime(available_level=FeatureLevel.LOCAL_MODEL, dependencies={"provider": True})

    assert offline.check("manifest_validate").allowed is True
    assert offline.check("rewrite").allowed is False
    assert local.check("rewrite").allowed is True
