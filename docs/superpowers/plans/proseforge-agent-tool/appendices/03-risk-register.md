# Risk Register

## Engineering Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| ProseForge root moves | Adapter cannot find engine | Explicit config and validation |
| ProseForge wrapper output is not JSON | Adapter parse fails | Preserve raw stdout |
| Windows path quoting issues | Commands fail | Use list-form subprocess arguments |
| UTF-8 console issues | Reports unreadable | Read/write files with UTF-8 and capture raw output |
| Provider API differences | Model calls fail | Provider kind abstraction and injected transport tests |
| Domestic endpoint changes | Config breaks | Do not hard-code domestic endpoints |
| Local model endpoint unavailable | Draft fails | Provider error with retry and prompt pack |
| Memory grows noisy | Bad retrieval | Ranking, compaction, source references |
| Retrieval misses canon | Continuity errors | ProseForge post/review still gate output |
| Workflow interruption | Lost work | Save state after every step |
| Draft overwritten | Lost writing | Versioned draft writer |
| Accept ingests bad rewrite | Novel damage | Empty rewrite block, accept result capture, guard rerun |

## Product Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Daily workbook too generic | User stops using it | Date, target, evidence, closeout required |
| Plan too large again | Execution slows | Keep index plus small files |
| Too many knobs | User confused | Ship examples and defaults |
| Model choice dominates workflow | Inconsistent output | Role-based routing |
| Agent becomes prompt-only | Loses professional workflow | Every model call must attach evidence and workflow state |

## Release Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Tests only cover happy path | Hidden failures | Add failure tests for config, provider, adapter, recovery |
| Real engine smoke mutates data | User data risk | Default smoke is status only |
| Generated local files committed | Repository bloat | Ignore workspace outputs later |
| Docs drift from commands | User confusion | CLI tests and docs audit before release |

## Maintainability And Late-Stage Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Bugs pile up in late subsystems | A broken module blocks the whole product | Capability flags + safe-mode boot (Task 66): disable the module, ship degraded |
| A subsystem cannot be fixed in time | Release stalls | Three-tier rollback (`architecture/10`): revert the card commit, restore migration backup, or disable the capability |
| Cross-module change breaks a distant module | Late, hard-to-locate integration bugs | Contract tests per boundary + golden snapshots (Task 67); CI runs them every change (Task 64) |
| Internal interface drifts | Silent breakage across subsystems | Interface compatibility policy (`architecture/10`): contract test updated in the same commit, one-version shim before removal |
| One subsystem corrupts another's data | Data loss spreads | Blast-Radius Contract (`architecture/10`); writes isolated behind stores; shared lock (Task 65); migration backup (Task 53) |
| Fault is hard to diagnose | Slow repair | Debugging runbook (`architecture/10`): trace id (Task 40) → event log → support bundle (Task 58) → isolate with canonical fakes (Task 67) |
| Drifting per-card test fakes | Inconsistent test coverage | One authoritative fakes module (Task 67) reused across cards |
| Autonomous loop runs away | Wasted cost, stuck process | Iteration + cost budget (Tasks 68/61), no-progress detector, interruptibility (Task 74), capability disable (Task 66) |
| Tool execution harms the system | Data loss or unsafe commands | Workspace confinement + sandbox + approval (Tasks 71/72), permission ceiling (Task 33), injection guard (Task 62) |
| Sub-agent escalates permissions | Privilege escape | Ceiling clamped to parent grant; isolated context (Task 73) |
| Agent quality regresses silently | Lower task success over time | Task-success eval harness as a release gate (Tasks 75/60/64) |

## Risk Review Cadence

Review this file:

- After Task 03.
- After Task 07.
- After Task 13.
- Before Task 17 release hardening.
- After Task 40 (runtime now has chat, background jobs, and concurrency — re-check fault isolation and blast radius).
- Before Task 60 (release gate — re-check maintainability: capabilities, rollback paths, contract/golden coverage).
