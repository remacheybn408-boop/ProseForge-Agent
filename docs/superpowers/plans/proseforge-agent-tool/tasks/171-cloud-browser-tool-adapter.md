# Task 171: Cloud Browser Tool Adapter

## Goal

Add a cloud browser tool adapter for non-desktop browsing tasks through a managed or injected backend.

## Architecture Notes

This is not desktop control. The browser backend is remote or headless and exposes typed actions, screenshots, DOM snapshots, downloads, and navigation under URL safety and permission policy.

## Files

- Create `src/proseforge_agent/tools/managed/cloud_browser.py`.
- Add tests in `tests/tools/test_cloud_browser_tool_adapter.py`.
- Add fixtures under `tests/tools/fixtures/cloud-browser/`.

## Interfaces / Contracts

- `CloudBrowser.open(url)`, `snapshot()`, `click(selector)`, `type(selector, text)`, `download(ref)`, and `close()`.
- `pf-agent browser check --provider fake`
- Browser actions emit trace events and bounded artifacts.

## TDD Steps

- [ ] Write failing test `tests/tools/test_cloud_browser_tool_adapter.py::test_browser_navigation_requires_url_safety`.
- [ ] Run `python -m pytest tests/tools/test_cloud_browser_tool_adapter.py::test_browser_navigation_requires_url_safety -q` and confirm failure.
- [ ] Implement fake browser backend, URL safety integration, action results, and artifact refs.
- [ ] Run the targeted test and confirm pass.
- [ ] Add companion tests for blocked navigation, screenshot artifacts, DOM limits, download approval, and cleanup.
- [ ] Run `python -m pytest tests/tools/test_cloud_browser_tool_adapter.py -q` and `python -m pytest -q`.
- [ ] Commit with `feat: add cloud browser tool adapter`.

## Verification

```powershell
python -m pytest tests/tools/test_cloud_browser_tool_adapter.py -q
pf-agent browser check --provider fake
python -m pytest -q
```

## Acceptance

- Browser actions are typed, bounded, and permission-gated.
- URL safety runs before navigation.
- Screenshots and downloads are artifact references, not unbounded prompt text.
- No desktop automation dependency is introduced.

## Commit Boundary

Commit only Task 171 browser adapter files, tests, fixtures, and CLI wiring. Do not bundle adjacent task cards.

