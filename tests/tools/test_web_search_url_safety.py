"""Web search and URL safety managed tool tests (Task 170)."""

from __future__ import annotations

import json

from proseforge_agent.cli import main
from proseforge_agent.tools.managed.url_safety import UrlSafetyPolicy
from proseforge_agent.tools.managed.web_search import FakeWebSearchProvider


def test_search_results_are_cited_and_not_canon():
    provider = FakeWebSearchProvider()

    response = provider.search("ProseForge demo")

    assert response.query == "ProseForge demo"
    assert response.results
    assert response.results[0].citation_id == "web-1"
    assert response.results[0].is_canon is False
    assert response.results[0].to_citation()["url"].startswith("https://")


def test_url_safety_blocks_denied_domains_and_limits_content():
    policy = UrlSafetyPolicy(
        allowed_domains={"example.com"},
        denied_domains={"blocked.example"},
        allowed_mime_types={"text/html"},
        max_content_bytes=1024,
    )

    blocked = policy.check("https://blocked.example/page")
    oversized = policy.check("https://example.com/page", content_length=2048)
    unsupported = policy.check("https://example.com/file.zip", mime_type="application/zip")
    allowed = policy.check("https://example.com/page", mime_type="text/html", content_length=512)

    assert blocked.status == "blocked"
    assert oversized.status == "blocked"
    assert unsupported.status == "unsupported"
    assert allowed.status == "allowed"


def test_web_search_cli_json(capsys):
    assert main(["search", "ProseForge demo", "--provider", "fake", "--json"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["title"] == "Web Search"
    assert payload["data"]["results"][0]["is_canon"] is False
    assert payload["data"]["citations"][0]["id"] == "web-1"
