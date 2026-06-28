# Task 66: Capability Flags And Safe-Mode Boot

## Goal

Let any subsystem be turned off through config, and auto-disable a subsystem that fails its startup self-check so the rest of the product keeps running.

## Agent Product Requirement

When a subsystem has bugs that cannot be fixed in time, the product must still ship and run with that capability disabled — degraded, not down.

> Dependency note: execute after the installation doctor (Task 42) and the event bus (Task 40). Logical position: 42.5.

## Architecture Notes

`capabilities` is a top-level core module that gates every optional subsystem (chat, service API, local models, planning, providers, memory, retrieval, workflow). It reads capability flags from config, runs a lightweight self-check per subsystem at boot (reusing the doctor's `DoctorCheck` type, Task 42), and produces a resolved capability map. A subsystem whose self-check fails is set to `disabled`, an event is emitted (Task 40), and the CLI continues in safe mode running every still-healthy capability. Calling a disabled capability returns a readable message plus a recovery command and a trace id — never a stack trace. This module implements the Blast-Radius Contract in `architecture/10-modularity-and-recovery.md`.

Read before starting:

- ../architecture/02-system-architecture.md (Dependency Direction, Error Boundaries)
- ../architecture/10-modularity-and-recovery.md (Blast-Radius Contract)
- 00-task-index.md

## Files

- Create `src/proseforge_agent/capabilities.py`
- Create `tests/test_capabilities.py`
- Create `tests/fixtures/capability-flags-and-safe-mode/capabilities.yaml`

## Interfaces / Contracts

- `CapabilityRegistry(config, checks).boot() -> CapabilityMap` resolves every capability to `enabled` | `degraded` | `disabled` with a reason.
- A capability whose self-check raises is recorded as `disabled` with the reason; `boot()` never propagates the exception.
- `CapabilityMap.require(name) -> None` raises `ConfigurationError` with a recovery command when a disabled capability is invoked.
- Core capabilities (`config`, `cli`, `capabilities`, `concurrency`, `errors`) are never disable-able; everything else is.

## Data Flow

1. Load capability flags from config (default: all non-core enabled).
2. For each capability, run its registered self-check.
3. Mark each `enabled`, `degraded`, or `disabled` with a reason.
4. Emit a safe-mode event listing any auto-disabled capability.
5. Return the `CapabilityMap`; callers gate features through `require()`.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_capabilities.py::test_failing_subsystem_self_check_is_auto_disabled_not_fatal`**

```python
def test_failing_subsystem_self_check_is_auto_disabled_not_fatal():
    checks = {
        "chat": lambda: (_ for _ in ()).throw(RuntimeError("boom")),  # chat self-check fails
        "workflow": lambda: None,                                      # workflow is healthy
    }
    cap_map = CapabilityRegistry(config={}, checks=checks).boot()  # must not raise
    assert cap_map.status("chat") == "disabled"
    assert cap_map.status("workflow") == "enabled"
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/test_capabilities.py::test_failing_subsystem_self_check_is_auto_disabled_not_fatal -q
```

Expected: FAIL because `CapabilityRegistry` and `CapabilityMap` are missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement `CapabilityRegistry`, `CapabilityMap`, flag loading, per-capability self-check, safe-mode boot, and `require()`.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/test_capabilities.py::test_failing_subsystem_self_check_is_auto_disabled_not_fatal -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

```text
test_disabling_chat_leaves_writing_workflow_enabled
test_calling_disabled_capability_returns_recovery_message_not_traceback
test_cli_flag_overrides_config_capability_value
test_safe_mode_emits_event_for_each_auto_disabled_capability
test_core_capabilities_cannot_be_disabled
test_disable_reason_supports_utf8_chinese_text
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_capabilities.py -q
pf-agent status --capabilities
```

Expected: tests pass and `status --capabilities` lists each capability as enabled/degraded/disabled with a reason.

- [ ] **Step 7: Run cross-platform contract check**

```powershell
python -m pytest tests/test_capabilities.py -q
```

Expected: PASS using simulated configs and self-checks on any host.

- [ ] **Step 8: Record commit boundary**

```powershell
git add src/proseforge_agent/capabilities.py tests/test_capabilities.py tests/fixtures/capability-flags-and-safe-mode
git commit -m "feat: add capability flags and safe-mode boot"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Cross-Platform Notes

- Flags and reasons are UTF-8 data with no platform-specific paths.
- Self-checks reuse the doctor's `DoctorCheck` type for consistency.
- Works identically on Windows, macOS, and Linux.

## Failure Modes To Prove

- A subsystem self-check that raises auto-disables only that subsystem; boot does not crash.
- Disabling chat leaves the writing workflow usable.
- Invoking a disabled capability returns a recovery message and trace id, not a traceback.
- Core capabilities cannot be disabled.

## Verification

```powershell
python -m pytest tests/test_capabilities.py -q
pf-agent status --capabilities
```

## Acceptance

- Every non-core subsystem can be disabled via config or CLI flag.
- A failing subsystem is auto-disabled and the CLI runs in safe mode.
- Disabled-capability calls return recovery guidance, not stack traces.
- Auto-disable events are recorded for diagnostics.

## Commit Boundary

Commit only capability files and tests after verification passes. Wire other subsystems to `require()` only through their existing entry points.
