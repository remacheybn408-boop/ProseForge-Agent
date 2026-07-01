"""Cloud browser managed tool tests (Task 171)."""

from __future__ import annotations

from proseforge_agent.cli import main
from proseforge_agent.tools.managed.cloud_browser import CloudBrowser, FakeCloudBrowserBackend
from proseforge_agent.tools.managed.url_safety import UrlSafetyPolicy


def test_browser_navigation_requires_url_safety():
    browser = CloudBrowser(
        backend=FakeCloudBrowserBackend(),
        url_policy=UrlSafetyPolicy(denied_domains={"blocked.example"}),
    )

    blocked = browser.open("https://blocked.example/page")
    allowed = browser.open("https://example.com/page")

    assert blocked.status == "blocked"
    assert "denied" in blocked.reason
    assert allowed.status == "ok"
    assert allowed.trace[-1]["action"] == "open"


def test_browser_snapshot_and_download_are_bounded_artifacts():
    browser = CloudBrowser(backend=FakeCloudBrowserBackend())
    browser.open("https://example.com/page")

    snapshot = browser.snapshot()
    download = browser.download("report.pdf")

    assert snapshot.status == "ok"
    assert snapshot.artifact_refs[0].kind == "dom_snapshot"
    assert len(snapshot.summary) < 200
    assert download.artifact_refs[0].kind == "download"
    assert "raw_content" not in download.to_dict()


def test_browser_click_type_and_close_emit_trace_events():
    browser = CloudBrowser(backend=FakeCloudBrowserBackend())
    browser.open("https://example.com/page")

    clicked = browser.click("#submit")
    typed = browser.type("#title", "hello")
    closed = browser.close()

    assert clicked.status == "ok"
    assert typed.status == "ok"
    assert closed.status == "ok"
    assert [event["action"] for event in closed.trace][-3:] == ["click", "type", "close"]


def test_browser_cli_check(capsys):
    assert main(["browser", "check", "--provider", "fake"]) == 0

    out = capsys.readouterr().out
    assert "Cloud Browser" in out
    assert "snapshot" in out
