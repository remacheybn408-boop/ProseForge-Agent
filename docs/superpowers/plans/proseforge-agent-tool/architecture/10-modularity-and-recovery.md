# Modularity, Fault Isolation, And Recovery

## Goal

Keep ProseForge Agent maintainable as it grows to ~65 modules: a bug in one subsystem must not corrupt others, must be isolatable, and must be recoverable without rewriting the product. This document is the maintainer-facing contract. It consolidates guarantees that individual cards already make (Dependency Direction and Error Boundaries in `02-system-architecture.md`, recovery in Tasks 12/53, observability in Tasks 40/58) and adds the missing capability/safe-mode and contract-test guarantees (Tasks 66/67).

## Blast-Radius Contract

For any subsystem `X`:

1. **No cross-corruption.** A fault in `X` must never corrupt the persisted data of another subsystem. Writes are isolated behind store interfaces and serialized by the shared lock (Task 65).
2. **Disable-able.** `X` can be turned off through a capability flag (Task 66) without editing code; the rest of the product still boots and runs.
3. **Graceful degrade.** When `X` fails its startup self-check, it is auto-disabled and reported (safe mode), not allowed to crash the whole CLI.
4. **Explicit failure.** Calling a disabled or failed capability returns a readable message plus a recovery command and a trace id — never a bare stack trace.

This contract is enforced, not aspirational: Task 66 provides the runtime toggles and safe-mode boot, and Task 67's contract tests prove subsystem boundaries hold.

## Module Ownership Map

Each row lists a subpackage's responsibility, what it may depend on (see Dependency Direction in `02`), whether it can be disabled at runtime, and how it degrades. "Core" subsystems cannot be fully disabled; they degrade instead.

| Subpackage | Responsibility | Depends on | Disable-able | Degrade behavior on failure |
| --- | --- | --- | --- | --- |
| `config`, `errors`, `cli` | Entry, config load, typed errors | — | No (core) | `ConfigurationError` stops before writing artifacts |
| `capabilities` | Capability flags + safe-mode boot | config, doctor, events | No (core) | If it cannot read flags, default to safe mode (only core enabled) |
| `concurrency` | Shared file lock + SQLite retry | — | No (core) | Lock timeout raises clean error; no corruption |
| `adapters` (ProseForge engine) | Subprocess bridge to engine | config | No (core for writing) | `EngineAdapterError`; preserve stdout/stderr; mark step failed |
| `llm` | Provider protocol, routing, metering, streaming | config, secrets | Per-provider | `ProviderError`; save prompt pack; fallback router (Task 29); budget block (61) |
| `memory` | Agent memory store | concurrency | Degrade only | Memory write failure does not mark chapter accepted; record follow-up |
| `retrieval` | Evidence packs | memory, adapters (read) | Degrade only | Structured degraded result; workflow continues only if step permits |
| `workflow` | Run state, chapter lifecycle, recovery | adapters, retrieval, memory, llm, reports | Degrade only | State saved after every step; failed steps retry/resume |
| `planning` | Phase plans, daily workbooks | config, reports | Yes | Disabled → CLI reports the command is off with a recovery hint |
| `reports` | Markdown/JSON writers | — | No (core util) | Renderer error is contained to the report, not the run |
| `agent` | Kernel, intent, tools, permissions, safety, profiles, events | interfaces of llm/memory/retrieval/workflow/chat | Kernel is core for chat; tools per-tool | Permission/safety failure forces `read_only`; event write failure does not mark request complete |
| `chat` | Sessions, REPL, prompts, retrieval, memory, handoff | agent kernel | Yes (whole `chat` capability) | Disabled → writing workflows and CLI still work; chat command reports off |
| `service` | Optional local HTTP API | agent kernel | Yes | Disabled by default; never required by CLI |
| `install` | App dirs, doctor, secrets, native, packaging, QA | config, platform_io | Mostly yes | Doctor is read-only; a failing install check reports recovery, never mutates |
| `release` | Release gate aggregator | reports of other gates | Yes (dev only) | Missing/failing gate blocks release explicitly |
| `extension` | Registry for providers/steps/retrievers | contracts | Per-extension | Disabled/broken extension is isolated (Task 16), core unaffected |
| `testing` | Canonical fakes + contract harness | — | Test-only | Not shipped in runtime paths |

## Three-Tier Rollback

When something breaks, recover at the lowest sufficient tier:

1. **Code** — every task card is one commit (`feat: ...`). Revert the offending card's commit; dependents are later commits, so history stays bisectable. `git bisect` localizes a regression to a single card.
2. **Config / state** — migrations take a backup before any destructive change (Task 53); restore `backup_path`. Workflow state is saved after every step (Task 12) and is resumable. Capability flags can pin a subsystem off without touching code or data.
3. **Capability** — at runtime, disable the broken subsystem (Task 66) and keep shipping/using the rest. This is the answer to "the bug can't be fixed in time": run degraded, not down.

## Debugging Runbook

Standard path when a user or test reports a failure:

1. **Trace id** — every turn/step/job emits a trace id (Task 40). Get it from the error message or report.
2. **Event log** — filter the event JSONL by trace id to see the exact step that failed and its severity.
3. **Support bundle** — `pf-agent support bundle --redact` (Task 58) collects doctor report, recent traces, provider status, config shape, OS info — one shareable, secret-free artifact.
4. **Isolate** — reproduce with the canonical fakes (Task 67) to confirm whether the fault is in the subsystem or its dependency; the failing contract test names the broken boundary.
5. **Contain** — if no quick fix, disable the capability (Task 66) so the rest stays usable.
6. **Roll back** — revert the card commit (tier 1) and/or restore from migration backup (tier 2).

## Internal Interface Compatibility Policy

As subsystems evolve, cross-subsystem interfaces (the contracts in `02` "First Release Interfaces" and "Hardening Interfaces") are the stable seams:

- A change to a shared interface must first update or add its contract test (Task 67) in the same commit, so breakage is loud and local.
- Removing or renaming an interface method requires a one-version compatibility shim (keep the old signature delegating to the new) before deletion.
- New optional behavior is added as new methods/fields, not by changing existing signatures, so dependents do not break silently.

## Acceptance Criteria

- Every subpackage in the ownership map has a defined disable/degrade behavior.
- No subsystem fault can corrupt another subsystem's persisted data.
- Any subsystem can be disabled (or degrades) without crashing the CLI.
- Every failure path yields a trace id and a recovery command.
- Each cross-subsystem interface has a backing contract test before it is changed.
