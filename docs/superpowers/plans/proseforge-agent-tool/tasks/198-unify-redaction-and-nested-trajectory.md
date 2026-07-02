# Task 198: Unify Redaction + Nested Trajectory Redaction / 统一脱敏

## Goal

Close the secret-leak gap in the shared redactor. `agent/events.py:_redact`
(consumed by observability, the event bus JSONL, the background job runner, and
trajectory export) only inspects **dict keys** — a secret that lives inside a
**string value** (e.g. `{"log_line": "Authorization: Bearer sk-…"}`) is emitted
in cleartext. Meanwhile `mcp/credentials.py:redact_sensitive` already scans
string values correctly but is a **duplicate**. Unify on the string-scanning
implementation, expand the sensitive-key list, and fix trajectory
`text_fields` redaction to recurse into nested structures.

## Architecture Notes

Fixes **findings 1.8 + 3.1** (Critical · Security, duplicate/incomplete
redaction) and **3.2** (Medium · Security, nested trajectory fields) of
`docs/review/core-review-2026-07-01.md`.

Current state (verified):

- `agent/events.py:14` `_SENSITIVE_KEY_PARTS = ("api_key", "token", "secret",
  "password", "authorization")`.
- `agent/events.py:147` `_redact` recurses dict/list; **string leaves returned
  verbatim**.
- `mcp/credentials.py:39` `redact_sensitive` scans strings via assignment /
  token regexes — the correct behavior.
- `eval/trajectories.py:118` `_redact_with_text` runs `_redact` then sweeps
  `text_fields` only against **top-level keys**; nested `outputs.data.text`
  leaks.

Design:

1. Make `mcp/credentials.redact_sensitive` (string-scanning) the **single
   source of truth**. Either move it to `agent/events.py` and have
   `mcp/credentials.py` re-export, or have `events._redact` delegate to it.
   Keep one public name; deprecate the duplicate with a thin alias.
2. Expand the sensitive-key parts to include: `bearer, cookie, refresh_token,
   client_secret, private_key, session_token, credential` (in addition to the
   existing five).
3. The unified redactor MUST, for every string value at any depth: redact
   `Authorization: Bearer …`, `api_key=…`, and `sk-…`-style tokens.
4. Fix `_redact_with_text` to recurse: replace `text_fields` matches at every
   depth in nested dicts/lists, not just top-level keys.
5. Keep the redaction sound paths already covered by 183/185
   (`release/publish.py`, `install/installers.py`) untouched — they route
   secrets via env and are not affected.

Read before starting:

- `docs/review/core-review-2026-07-01.md` (findings 1.8, 3.1, 3.2; note 3.3)
- 181-observer-hooks-and-telemetry-export.md
- 182-middleware-hooks-and-trajectory-datasets.md
- 121-mcp-credential-boundary.md
- `src/proseforge_agent/agent/events.py`, `mcp/credentials.py`,
  `eval/trajectories.py`

## Files

- Modify `src/proseforge_agent/agent/events.py` (unify `_redact`, expand
  `_SENSITIVE_KEY_PARTS`).
- Modify `src/proseforge_agent/mcp/credentials.py` (single implementation +
  compatibility alias).
- Modify `src/proseforge_agent/eval/trajectories.py` (`_redact_with_text`
  recursion).
- Add tests in `tests/test_unified_redaction.py`.

## Interfaces / Contracts

- The shared redactor redacts secrets in string **values** at any depth.
- `_SENSITIVE_KEY_PARTS` includes the seven new parts.
- Trajectory `redact_text_fields=("text",)` redacts `outputs.data.text` and
  `outputs.results[0].text`, not only a top-level `text`.
- No public name is removed without a re-export alias (back-compat).

## Data Flow

1. An observer emits `payload={"raw_http_response": "…Authorization: Bearer
   sk-xxx…"}`.
2. `events._redact(payload)` scans the string value → token replaced.
3. Telemetry / trajectory JSONL contains `[redacted]`, never the token.

## TDD Steps

- [ ] **Step 1: Write failing test
  `tests/test_unified_redaction.py::test_redact_scans_secret_inside_string_value`**

```python
def test_redact_scans_secret_inside_string_value():
    payload = {"log_line": "Authorization: Bearer sk-super-secret-123"}
    out = _redact(payload)
    assert "sk-super-secret-123" not in json.dumps(out)
    assert "Bearer" not in json.dumps(out) or "[redacted]" in json.dumps(out)
```

- [ ] **Step 2: Run the targeted test and confirm failure** (today the Bearer
  token survives because `log_line` matches no sensitive key).

- [ ] **Step 3: Unify on the string-scanning redactor, expand key parts, fix
  trajectory recursion.**

- [ ] **Step 4: Run the targeted test and confirm pass.**

- [ ] **Step 5: Companion tests**

```text
test_expanded_sensitive_keys_are_redacted_by_key            # cookie, refresh_token, ...
test_trajectory_nested_text_field_is_redacted
test_trajectory_list_nested_text_field_is_redacted
test_mcp_credentials_redact_sensitive_still_available       # alias back-compat
test_release_publish_redaction_unchanged                    # finding 3.3 regression guard
```

- [ ] **Step 6: Subsystem verification**

```powershell
python -m pytest tests/test_unified_redaction.py tests/test_observer_hooks_and_telemetry_export.py tests/test_middleware_hooks_and_trajectory_datasets.py -q
```

- [ ] **Step 7: Full repository verification**

```powershell
python -m pytest -q
```

- [ ] **Step 8: Commit boundary**

```powershell
git add src/proseforge_agent/agent/events.py src/proseforge_agent/mcp/credentials.py src/proseforge_agent/eval/trajectories.py tests/test_unified_redaction.py
git commit -m "fix: unify secret redaction across events and trajectories"
```

## Failure Modes To Prove

- A Bearer token embedded in a string value is redacted in telemetry export.
- A nested `outputs.data.text` private draft is redacted on trajectory export.
- The existing MCP credential-boundary tests and release/publish redaction
  tests remain green (no regression, no double-redaction breakage).

## Verification

```powershell
python -m pytest tests/test_unified_redaction.py -q
python -m pytest -q
```

## Acceptance

- `events._redact` and `mcp/credentials.redact_sensitive` share one
  string-scanning implementation; secrets in string values are redacted.
- `_SENSITIVE_KEY_PARTS` expanded; trajectory nested-field redaction recurses.
- Full suite green; new tests added; no public API removed without alias.

## Commit Boundary

Commit only the redaction unification, key-list expansion, trajectory recursion
fix, and tests. Do not bundle 199's tool fixes.
