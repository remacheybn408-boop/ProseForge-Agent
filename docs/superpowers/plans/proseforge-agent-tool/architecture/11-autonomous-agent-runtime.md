# Autonomous Agent Runtime

## Goal

Give ProseForge Agent the runtime maturity of a complete autonomous agent (in the class of Claude Code / Codex / coding agents) while keeping long-form novel writing as the first vertical capability. The per-turn kernel (Task 31) answers one turn; this layer adds the autonomous multi-step loop, task decomposition, self-verification, a general tool framework with a sandbox, sub-agent delegation, interruptibility, and an evaluation harness (Tasks 68–75). The runtime is general-purpose; writing is the first capability built on it, not a special case baked into it.

## Runtime Layers

```text
User surface (CLI chat / REPL / future UI / local API)
        |
        v
Agent Loop (Task 68)            multi-step plan -> act -> observe -> verify -> repeat/stop
        |  uses
        +-- Task Planner / TODO (Task 69)     decompose goal into tracked sub-tasks
        +-- Agent Kernel (Task 31)            executes one turn (intent, tools, provider)
        +-- Self-Verification / Reflection (Task 70)  check output, reflect, retry
        +-- Tool Framework (Task 71)          fs / web / domain tools through the registry
        +-- Tool Sandbox + Approval (Task 72) gate command/code execution
        +-- Sub-Agent Delegation (Task 73)    scoped, isolated sub-tasks
        +-- Interrupt / Steering (Task 74)    cooperative cancel + redirect
        +-- Event Bus (Task 40)               every step traced
        |
        v
Vertical capabilities (novel-writing workflows now; other verticals later)
```

The kernel stays single-turn and unchanged; the loop orchestrates many kernel turns. This keeps the kernel testable in isolation and the loop responsible for stop conditions and budgets.

## Control Flow Of An Autonomous Run

```text
run(goal)
  -> plan: decompose goal into sub-tasks (Task 69)
  -> loop until done / budget / no-progress / interrupted:
       -> select next sub-task
       -> act: kernel.run_turn (intent -> tool/provider) (Task 31)
       -> observe: capture result + events (Task 40)
       -> verify: check against the sub-task's criteria (Task 70)
            -> fail: reflect and retry within budget
            -> pass: mark sub-task done (Task 69)
       -> compact working context if over threshold (Task 68)
       -> check interrupt/steer signal (Task 74)
  -> return LoopResult (status, steps, final output, transcript)
```

## Budgets And Safety Guardrails

An autonomous loop must never run away or act unsafely. Every run is bounded by:

- **Iteration budget** — hard cap on loop turns; exceeding it stops with `stopped_budget`.
- **Cost/token budget** — reuses the metering/budget policy (Task 61); a budget block stops the run and preserves state.
- **No-progress detector** — repeated non-advancing turns stop with `stopped_no_progress`.
- **Permission ceiling + sandbox** — tools that write or execute are gated by the permission policy (Task 33), the prompt-injection guard (Task 62), and the execution sandbox (Task 72).
- **Interruptibility** — the user can stop or redirect at any safe point (Task 74).
- **Capability gating** — the whole autonomous runtime is a capability that can be disabled or safe-moded (Task 66).

## Writing As The First Vertical

The chapter lifecycle (Tasks 13/14) is expressed on this runtime, not parallel to it:

- A chapter goal decomposes into sub-tasks (retrieve evidence → draft → post → review → revise → accept) via the Task Planner (69).
- ProseForge `post`/`review` register as **domain verifiers** in the self-verification framework (70); a failed guard triggers reflection/rewrite rather than a silent accept.
- Drafting tools and the ProseForge engine adapter are tools in the framework (71), gated by the sandbox/approval policy (72) for any mutating engine command.
- Long chapter runs use working-context compaction (68) and remain interruptible (74).

This means the writing workflow inherits autonomy, verification, budgets, and interruptibility for free, and future verticals (e.g. a code vertical) reuse the same runtime.

## Module Map (additions to `02-system-architecture.md`)

| Module | Responsibility | Task |
| --- | --- | --- |
| `agent/loop.py` | Multi-step autonomous loop, stop conditions, context compaction | 68 |
| `agent/planner.py` | Goal decomposition + TODO tracking | 69 |
| `agent/reflection.py` | Self-verification + reflection/retry; pluggable domain verifiers | 70 |
| `agent/tools.py` (extended) | General tool framework: fs/web + domain tools | 71 |
| `agent/sandbox.py` | Execution sandbox + approval policy | 72 |
| `agent/subagent.py` | Scoped sub-agent delegation | 73 |
| `agent/control.py` | Interrupt + steering tokens | 74 |
| `agent/eval.py` | Task-success eval harness | 75 |

See `10-modularity-and-recovery.md` for how these fit the blast-radius contract and three-tier rollback, and `02-system-architecture.md` for the dependency direction these modules must respect.

## Acceptance Criteria

- An autonomous run is bounded by iteration and cost budgets and a no-progress detector.
- The loop reuses the per-turn kernel without modifying it.
- Output is self-verified against per-sub-task criteria; failures trigger bounded reflection/retry.
- Write/execute tools are gated by permission, safety, sandbox, and approval.
- A run can be interrupted or steered at a safe point without losing state.
- The novel-writing workflow runs as a vertical on this runtime, with ProseForge gates as domain verifiers.
- Agent-level task success is measurable through the eval harness.
