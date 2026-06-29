# Task 170: Web Search And URL Safety Tools

## Goal

Add web search and URL safety tools behind the managed tool gateway.

## Architecture Notes

Search results are evidence candidates, not canon. URL fetching must apply allow/deny policy, content limits, MIME checks, and citation metadata.

## Files

- Create `src/proseforge_agent/tools/managed/web_search.py`.
- Create or extend `src/proseforge_agent/tools/managed/url_safety.py`.
- Add tests in `tests/tools/test_web_search_url_safety.py`.

## Interfaces / Contracts

- `pf-agent search "query" --provider fake --json`
- `WebSearchResult` includes title, url, snippet, source, fetched_at, and trust metadata.
- URL safety classifies allowed, blocked, requires_confirmation, or unsupported.

## TDD Steps

- [ ] Write failing test `tests/tools/test_web_search_url_safety.py::test_search_results_are_cited_and_not_canon`.
- [ ] Run `python -m pytest tests/tools/test_web_search_url_safety.py::test_search_results_are_cited_and_not_canon -q` and confirm failure.
- [ ] Implement fake search backend, URL safety checks, evidence conversion, and CLI output.
- [ ] Run the targeted test and confirm pass.
- [ ] Add companion tests for blocked URLs, oversized pages, unsupported MIME, redirects, and missing network capability.
- [ ] Run `python -m pytest tests/tools/test_web_search_url_safety.py -q` and `python -m pytest -q`.
- [ ] Commit with `feat: add web search and url safety tools`.

## Verification

```powershell
python -m pytest tests/tools/test_web_search_url_safety.py -q
pf-agent search "ProseForge demo" --provider fake --json
python -m pytest -q
```

## Acceptance

- Search output is citation-ready and never accepted as canon automatically.
- URL safety blocks unsafe or unsupported fetches.
- Fake provider path is deterministic.
- Network-disabled mode degrades clearly.

## Commit Boundary

Commit only Task 170 search, URL safety, tests, fixtures, and CLI wiring. Do not bundle adjacent task cards.

