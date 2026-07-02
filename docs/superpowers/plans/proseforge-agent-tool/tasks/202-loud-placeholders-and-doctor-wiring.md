# Task 202: Loud Placeholders + `doctor --section wiring` / 占位传输显式化

## Goal

Make "contract-only" transports fail loud instead of silently succeeding, and
add a `pf-agent doctor --section wiring` that reports, per subsystem, whether a
**real** transport or a **placeholder** is currently bound. Today a machine
without a real MCP / gateway / execution transport returns
`{"ok": False, "error": "…not configured"}` (MCP), `delivered=True` (gateway),
or a dry-run plan (execution) — all indistinguishable from real success/failure
in telemetry.

## Architecture Notes

Fixes **findings 4.1, 4.2, 4.3** (High · Architecture) and addresses **5.2**
(the `--offline` flag is the wrong axis; the axis is "real transport wired vs
not") of `docs/review/core-review-2026-07-01.md`.

Design:

1. **MCP** (`mcp/client.py`): `StdioMCPTransport.start()` (and the HTTP/SSE
   `PlaceholderMCPTransport`) raise `ConfigurationError("stdio MCP transport is
   a placeholder; wire a real transport before production")` unless
   `PF_AGENT_ALLOW_PLACEHOLDER_MCP=1` is set. `StaticMCPTransport` (test double)
   is unaffected.
2. **Gateway** (`gateway/platforms/*.py`): each adapter gains
   `allow_fake_transport: bool = False`. `send/edit` refuse to return
   `delivered=True` unless a real `_client` is wired OR
   `allow_fake_transport=True`. Without either, return
   `SendResult(delivered=False, retryable=False, error="fake transport; set
   allow_fake_transport or wire a real client")`.
3. **Execution** (`environments/*.py`): backends refuse to report success for
   `dry_run=False` unless a real command runner is injected — return a
   distinguished "planner only" error (or raise at construction). Keep
   `dry_run=True` plans working.
4. **Doctor** (`install/doctor.py`): add a `wiring` section that lists each
   subsystem (mcp, gateway.<platform>, environment.<backend>) and whether it is
   `real`, `placeholder`, or `test-double`, plus the env flag that would change
   it. Wire it into `pf-agent doctor --section wiring`.

Preserve determinism: the default test suite uses test doubles
(`StaticMCPTransport`, fake gateway clients, dry-run plans) which remain valid;
only production placeholders go loud.

Read before starting:

- `docs/review/core-review-2026-07-01.md` (findings 4.1, 4.2, 4.3, 5.2)
- 116–121 (MCP), 155–161 (gateway), 162–168 (execution), 42/doctor card
- `src/proseforge_agent/mcp/client.py`, `gateway/platforms/*.py`,
  `environments/*.py`, `install/doctor.py`, `cli.py` (`_handle_doctor`)

## Files

- Modify `src/proseforge_agent/mcp/client.py` (placeholder `.start()` guard).
- Modify `src/proseforge_agent/gateway/platforms/*.py` (base + adapters:
  `allow_fake_transport`).
- Modify `src/proseforge_agent/environments/*.py` (refuse fake real-run).
- Modify `src/proseforge_agent/install/doctor.py` (+ `cli.py` doctor section).
- Add tests in `tests/test_loud_placeholders_and_wiring.py`.

## Interfaces / Contracts

- Production placeholder MCP transports raise on `.start()` unless the env flag
  is set; test doubles never raise.
- Gateway adapters do not claim `delivered=True` from a fake transport without
  explicit opt-in.
- Execution backends do not report success for `dry_run=False` without a real
  runner.
- `pf-agent doctor --section wiring` reports transport binding per subsystem.

## Data Flow

1. Operator runs `pf-agent doctor --section wiring` → sees `mcp: placeholder`,
   `gateway.telegram: fake`, `environment.docker: planner`.
2. A real MCP call via a placeholder transport now raises clearly instead of a
   generic "tool failed".

## TDD Steps

- [ ] **Step 1: Write failing test
  `tests/test_loud_placeholders_and_wiring.py::test_doctor_wiring_section_reports_transport_bindings`**

```python
def test_doctor_wiring_section_reports_transport_bindings():
    report = InstallationDoctor().run(section="wiring")
    names = {c.name for c in report.checks}
    assert "mcp" in names
    assert any(c.name.startswith("gateway.") for c in report.checks)
    assert any(c.name.startswith("environment.") for c in report.checks)
```

- [ ] **Step 2: Run the targeted test and confirm failure** (no `wiring`
  section today).

- [ ] **Step 3: Add the doctor wiring section + the three loudness guards.**

- [ ] **Step 4: Run the targeted test and confirm pass.**

- [ ] **Step 5: Companion tests**

```text
test_placeholder_mcp_start_raises_without_env_flag
test_placeholder_mcp_start_allowed_with_env_flag
test_gateway_adapter_refuses_delivered_true_from_fake_transport
test_execution_backend_refuses_real_run_without_runner
test_cli_doctor_section_wiring_smoke
```

- [ ] **Step 6: Subsystem verification**

```powershell
python -m pytest tests/test_loud_placeholders_and_wiring.py tests/test_mcp_*.py tests/test_gateway_*.py tests/test_environments_*.py -q
```

- [ ] **Step 7: Full repository verification**

```powershell
python -m pytest -q
```

- [ ] **Step 8: Commit boundary**

```powershell
git add src/proseforge_agent/mcp/client.py src/proseforge_agent/gateway/platforms src/proseforge_agent/environments src/proseforge_agent/install/doctor.py src/proseforge_agent/cli.py tests/test_loud_placeholders_and_wiring.py
git commit -m "fix: make placeholder transports loud and add doctor wiring section"
```

## Cross-Platform Notes

- The env flag `PF_AGENT_ALLOW_PLACEHOLDER_MCP` must be respected on all OSes.
- Doctor output must be UTF-8 safe (relies on Task 190 bootstrap).

## Failure Modes To Prove

- A production MCP placeholder `.start()` raises without the flag, passes with
  it.
- A fake gateway transport cannot report delivery without opt-in.
- `dry_run=False` on a runner-less execution backend does not fake success.
- `doctor --section wiring` enumerates all three subsystem families.

## Verification

```powershell
python -m pytest tests/test_loud_placeholders_and_wiring.py -q
python -m pytest -q
```

## Acceptance

- Placeholders are visible: they raise or refuse, and `doctor --section wiring`
  reports bindings.
- Test doubles and `dry_run=True` paths keep working; full suite green; new
  tests added.

## Commit Boundary

Commit only the loudness guards, the doctor wiring section, and the tests. Do
not bundle 197's client policy enforcement (they are complementary but separate
commits).
