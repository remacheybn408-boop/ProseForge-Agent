# Core Code Review — 2026-07-01

> Scope: `src/proseforge_agent/` at commit `769d133`. Reviewer: Claude Opus 4.7.
> Method: read + grep + 2 parallel subagents (independent 181–185 audit,
> coupling map). Focus: architecture, correctness, security, robustness.

## Executive Summary

Codebase is broadly sound (per Explore subagent: no circular imports, no
layering violations, no mutable-default traps, CLI lazily loads). Two
tracks of issue stand out and warrant hotfix cards before Task 186+ ships:

**Top 5 findings** (all Critical / High, all reproducible):

1. **[Critical · Architecture]** `MiddlewareRegistry` is **completely unwired** —
   `apply_tool_request` / `apply_tool_execution` have zero callers in the
   whole repo (grep confirms). Task 182's tests pass, but registering a
   middleware has no runtime effect. See finding **1.5**.
2. **[Critical · Architecture]** `MCPClient.call_tool` does **not** consult
   `MCPPolicy` before executing. Policy is only reached via the approval
   gate; a real transport wired in later runs untested. See **1.6**.
3. **[Critical · Security]** `agent/events.py._redact` (used by
   observability + trajectory + event bus) inspects only dict keys, never
   string values — so a payload like `{"log_line": "Authorization: Bearer
   sk-…"}` leaks in cleartext. `mcp/credentials.py` has the right
   implementation but they are duplicated. See **1.8**.
4. **[High · Security]** `_fs_edit` accepts `old=""` and blindly prepends
   `new` to any file. See **1.7**.
5. **[High · Correctness]** `MemoryStore` opens SQLite with
   `check_same_thread=True` (default) despite the module docstring
   promising cross-thread usage; second-thread access crashes. See **2.1**.

**Secondary Highs worth fixing this month**:

- **1.1** `ExecutionGuard.run` timeout is post-hoc, not enforcing — hangs
  block the runtime.
- **1.2** `InjectionGuard` Chinese regex triggers on ordinary novel prose.
- **1.9** `ToolRegistry.invoke` has zero callers; declared tools are stubs.
- **2.2** `IdempotencyStore` has lost-update race and non-atomic write.
- **4.1–4.3** MCP / gateway / execution placeholders silently succeed when
  transport is not wired — needs a `pf-agent doctor --section wiring`
  or explicit "not configured" errors to make the gap visible.

**Nothing else at Critical/High level** across the seven groups this pass.

## Findings by Group

### Group 1 — Agent Runtime Security Boundaries

**Reviewed**: `agent/permissions.py`, `agent/safety.py`, `agent/sandbox.py`,
`agent/execution_guard.py`, `agent/tools.py`, `agent/middleware.py`,
`agent/observability.py`, `mcp/{policy,approval,credentials}.py`.

#### 1.1 [High · Correctness] `ExecutionGuard.run` timeout is post-hoc, not real

**Location**: `agent/execution_guard.py:73-108`

The guard calls `func()` synchronously, then checks `elapsed >
timeout_seconds` after it returns. A blocked/hung `func` never returns and
never triggers the timeout — the timeout only fires when the call already
finished but took too long. Combined with `max_retries=0` default, a stuck
provider or MCP call can hang the whole runtime.

**Failure scenario**: A `provider.chat()` blocks forever on socket read.
`ExecutionGuard.run("openai", provider.chat)` never returns; the caller has
no way to abort. The name and public policy suggest an enforcing timeout;
the behavior is a stopwatch report.

**Fix direction**: Wrap `func()` in a `threading.Thread` with `.join(timeout)`
or use `concurrent.futures.ThreadPoolExecutor.submit(func).result(timeout)`;
on timeout, mark the future cancelled and record failure. For async callers,
provide an `arun()` using `asyncio.wait_for`.

#### 1.2 [Medium · Security-Robustness] `InjectionGuard` regex triggers on ordinary novel prose

**Location**: `agent/safety.py:52-61`

`_TOOL_INVOCATION_PATTERNS` includes a Chinese-only pattern
`re.compile(r"(现在)?(执行|运行|调用|启动)")` with NO word boundary, dotted
tool name, or context. Any sentence containing 执行/运行/调用/启动 as
ordinary verbs matches (very common in novels: "主角**执行**了命令",
"计划**启动**了", "系统**运行**中"). When such content flows in as
`provenance="untrusted"` (e.g. via attachment ingestion or workbook seeding),
the guard forces `allowed_ceiling` down to `read_only` for the whole turn,
denying legitimate writes.

**Failure scenario**: User ingests a chapter draft that includes 军事描写
with the verb 执行. Attachment ingestion emits it as untrusted content.
Any subsequent tool that requires `draft_write` is silently denied with the
reason "untrusted content contains injection patterns".

**Fix direction**: Require the tool-invocation pattern to co-occur with an
actual tool token (e.g. `[a-z_]+\.[a-z_]+` after the verb, mirroring the
English pattern on the same lines), or replace this pattern with the
already-defined one at `_TOOL_INVOCATION_PATTERNS[1]`. Add a false-positive
regression test with 3 novel-prose samples.

#### 1.3 [Low · Robustness] `Sandbox._preflight` conflates two failures into one message

**Location**: `agent/sandbox.py:135-148`

Both "insufficient permission ceiling" and "approval missing" return
`error="approval required"`. A caller receiving this cannot tell whether the
user needs to raise the ceiling first or just confirm; the recovery string
differs slightly but the machine-parseable `error` field is identical.

**Fix direction**: Return `error="insufficient_permission"` when the ceiling
gate fires and `error="approval_required"` only when approval itself is the
missing piece.

#### 1.4 [Note · Architecture] Policy authorizes tool NAME, not arguments — by design

**Location**: `agent/permissions.py:35-76`

`authorize(tool_name, permission_level, registry, session_context)` never
inspects tool arguments. Middleware rewrites that keep `tool_name` but
change `arguments` (e.g. `fs.read(path="notes.md") → fs.read(path="../../../etc/passwd")`)
therefore never trigger a re-authorization. This is **intentional at the
permission layer**; workspace containment lives inside `agent/tools.py`
`fs.read/fs.write/fs.edit` (Task 71). The follow-up question is whether
those tool bodies re-validate arguments — see finding 1.5.

_(This is a documented boundary, not a bug — recorded so subsequent
subagent findings can hang off it.)_

#### 1.5 [Critical · Architecture] Middleware system is **completely unwired**

**Location**: `agent/middleware.py:*`

`grep "apply_tool_request|apply_tool_execution"` across `src/proseforge_agent/`
returns **only middleware.py itself**. No caller anywhere in the codebase
invokes the middleware chain. Task 182 delivered a fully-tested contract
(101 lines of test) but the module is a dead subsystem — the `AgentKernel`,
tool dispatcher, and CLI handlers all bypass it. Users who register a
middleware (e.g., to redact prompts, add tracing, or gate risky tools) will
see it never run. This is a **Task 182 completion gap**, not a bug in the
middleware code.

**Failure scenario**: An operator registers a `tool_request` middleware
`redact_pii_from_arguments` believing it will scrub PII before tools see
it. It never fires; PII flows through.

**Fix direction**: Wire `MiddlewareRegistry.apply_tool_request` into the
tool dispatch path (add a helper `middleware_registry.apply_tool_request(req)`
before `PermissionPolicy.authorize` and re-authorize the rewritten request);
wire `apply_tool_execution` around the actual `tool.invoke`. Same for
LLM request/execution middleware around provider calls. Add an
integration test proving that a registered `tool_request` middleware fires
when a tool is dispatched via the kernel.

#### 1.6 [Critical · Architecture] MCP policy is not enforced by the MCP client

**Location**: `mcp/policy.py:38` `decide()`; `mcp/client.py:221` `call_tool`

`grep "MCPPolicy.decide|policy.decide"` finds callers only in
`mcp/approval.py`. `mcp/client.py:MCPClient.call_tool` executes any tool
name against the transport with **no policy check**. The intended data
flow — "client consults policy → approval gate → transport" — is broken
in the middle: only the approval gate reads the policy, and the client
does not consult the gate.

**Failure scenario**: A caller who does not manually route through
`MCPApprovalGate` (which is the default path in the CLI: check
`_handle_mcp` in cli.py) can call `MCPClient.call_tool("write_file",
{"path": "../../etc/passwd"})` — the transport is a placeholder so this
returns `{"ok": False, "error": "…not configured"}`, but the moment a real
stdio transport is wired in (Task 116 leaves this as pluggable), the
policy is silently absent.

**Fix direction**: In `MCPClient.__init__`, accept an optional `policy:
MCPPolicy | None` and an optional `approval_gate: MCPApprovalGate | None`.
In `call_tool`, when either is set, decide → enqueue-if-required → block
until decision. Document that a `MCPClient` constructed without a policy
is unsafe for production transports.

#### 1.7 [High · Security] `_fs_edit` accepts empty `old` and inserts arbitrary text at file head

**Location**: `agent/tools.py:175-183`

`_fs_edit` treats `payload["old"] == ""` as "found" (because
`"" in text` is always `True`), then `text.replace("", new, 1)` **prepends**
`new` to the file. A middleware, subagent, or crafted prompt that reaches
`fs.edit(path="canon.md", old="", new="<INJECTED>")` prepends attacker
content to any workspace file the session's ceiling allows.

**Failure scenario**: A `tool_request` middleware (or a compromised
subagent) mutates arguments to `old=""`. `fs.edit` reports success and
returns the workspace-relative path; the file has grown by one line at
the top.

**Fix direction**: Add `if not old: return ToolResult(ok=False,
error="old must be non-empty", provenance="workspace")` at the top of
`_fs_edit`. Add a companion test.

#### 1.8 [Critical · Security] `agent/events.py._redact` never inspects string values

**Location**: `agent/events.py:14, 147-159`; consumed by
`agent/observability.py:_build()`

`_redact` recurses only into dict/list; string leaves are returned
verbatim. `_SENSITIVE_KEY_PARTS = ("api_key", "token", "secret",
"password", "authorization")` — a payload key must contain one of these
substrings for its value to be replaced. But if a payload embeds a raw
log line or serialized dict as a string — e.g.
`payload = {"log_line": "Authorization: Bearer sk-super-secret"}` — the
`log_line` key matches nothing sensitive, and `_redact` returns the
Bearer token unchanged.

Meanwhile `mcp/credentials.py:redact_sensitive` — a **duplicate
redaction implementation** — DOES scan strings with `_ASSIGNMENT_RE`
and `_SECRET_TOKEN_RE`. So MCP surface is protected; observability
telemetry and trajectory datasets are not.

**Failure scenario**: An observer subscriber logs
`emit_provider_request(payload={"raw_http_response": "…Authorization:
Bearer sk-xxx…"})`. Telemetry JSONL contains the token in cleartext.
The Task 181 tests only check nested dict keys, not embedded string
values.

**Fix direction**: Unify redaction. Move `redact_sensitive` (with regex
scanning) from `mcp/credentials.py` to `agent/events.py`, or have
`events._redact` call it. Expand `_SENSITIVE_KEY_PARTS` to include
`bearer, cookie, refresh_token, client_secret, private_key,
session_token, credential`. Add a test where the raw log line
`"Authorization: Bearer sk-…"` appears in a string value.

#### 1.9 [High · Correctness] `ToolRegistry.invoke` has no callers — tools are dispatched by CLI, not registry

**Location**: `agent/tools.py:88` `ToolRegistry.invoke`

`grep tool_registry\.invoke|registry\.invoke\(` returns zero matches.
The `default_tool_registry()` declares 11 tools with names like
`memory.search`, `workflow.start`, `chapter.run` — but their `callable`
is a stub `_ok(name)` that just returns `{"ok": True, "tool": name,
"payload": payload}`. Real execution lives in CLI `_handle_*` functions.

This means:
1. Any code path that reaches the tool via `registry.invoke(name, …)`
   gets a NO-OP result — not a real execution.
2. `PermissionPolicy.authorize` checks these tools' declared
   `permission` fields (correct), but the executed behavior is
   elsewhere and may not enforce the same permission.
3. `default_tool_registry` is misleading for anyone reading the code
   to understand what tools do.

**Failure scenario**: A future subagent (or a wired middleware, once
1.5 is fixed) does `registry.invoke("chapter.run", {"slug": …})` and
receives `{"ok": True}` with no chapter drafted. The kernel proceeds
as if the write happened.

**Fix direction**: Either wire real handlers into `_ok` — thin
delegates that call the same functions the CLI handlers call — or
delete `default_tool_registry` and require callers to pass in a
registry with real callables. Mark stubbed tools with `enabled=False`
so the registry rejects `invoke` on them.

### Group 2 — Data Integrity and Concurrency

**Reviewed**: `concurrency.py`, `memory/store.py`, `memory/schema.py`,
`workflow/state.py`, `cron/core.py`.

#### 2.1 [High · Correctness] `MemoryStore` shares a SQLite connection across threads

**Location**: `memory/store.py:61` `sqlite3.connect(str(db_path))`

`sqlite3.connect` defaults to `check_same_thread=True`. `MemoryStore`
takes no thread hint and creates one connection at construction time.
The module docstring in `concurrency.py:2-4` states that chat, background
jobs, and the local API can all run at the same time and share the DB.
Any second-thread `.add()` / `.list()` / `.get()` raises
`sqlite3.ProgrammingError: SQLite objects created in a thread can only be
used in that same thread`.

**Failure scenario**: The Task 143 job runner emits a memory candidate
from a worker thread while the chat REPL holds the store on the main
thread. First cross-thread write crashes; may not appear in tests if the
suite is single-threaded.

**Fix direction**: Either pass `check_same_thread=False` and rely on the
`FileLock` + `PRAGMA busy_timeout` to serialize writes (simpler), or
adopt a per-thread connection pool. Either way, add a regression test
that spawns a thread and exercises `.add()`.

#### 2.2 [High · Correctness] `IdempotencyStore` has a lost-update race and non-atomic write

**Location**: `cron/core.py:64-84`

`remember(nonce)` does read-JSON → mutate → `write_text` with no lock and
no atomic rename. Two concurrent hosted-cron fires with different nonces
race: T1 loads {a}, T2 loads {a}, T1 saves {a,b}, T2 saves {a,c} — b is
lost. A crash between `open("w")` and buffer flush leaves a truncated
JSON file; the next `_load()` raises `json.JSONDecodeError` unhandled and
every subsequent `verify()` fails.

**Failure scenario**: Two cron fires arrive within the same second (or a
retry storm). One nonce is accepted twice because the second load didn't
see the first commit. The Task 180 "idempotent" claim is violated.

**Fix direction**: (a) wrap read-modify-write in `FileLock` from
`concurrency.py`; (b) write to `path.with_suffix(".json.tmp")` then
`os.replace(tmp, path)` for atomicity; (c) catch `json.JSONDecodeError`
in `_load()` and treat it as "no nonces yet" with a WARNING event.

#### 2.3 [Medium · Correctness] `FileLock` silently degrades to no-op on unusual platforms

**Location**: `concurrency.py:97-104`

If neither `fcntl` nor `msvcrt` is importable, the lock code path is
`pass`. On Termux Android, Alpine musl builds, or certain embedded
Python builds where both modules are absent (rare but exists), the lock
becomes a no-op — writers no longer serialize. This is a **silent**
correctness degradation with no log, no warning, no runtime check.

**Fix direction**: Either raise `LockError` at construction when both
primitives are unavailable, or emit a one-time warning via the event bus
and record `warnings["no_lock_primitive"] = True` for observability.

#### 2.4 [Low · Robustness] `with_sqlite_retry` matches error text with `in`

**Location**: `concurrency.py:132-133`

`if "database is locked" not in str(exc).lower()`. SQLite version drift
or a translated locale could shift this exact string; the retry path is
fragile. The stronger predicate is `sqlite3.OperationalError` with
`exc.sqlite_errorcode == sqlite3.SQLITE_BUSY` (Python 3.11+).

**Fix direction**: Prefer `sqlite_errorcode` check when available; keep
the string match as a fallback.

#### 2.5 [Note] `workflow/state.py` is well-shaped

**Location**: `workflow/state.py:1-100`

Transition table `ALLOWED` is explicit and validated before write; the
module docstring promises atomic writes via temp-file + `os.replace`
(need to confirm in write path but the pattern is correct). Uses
`concurrency.FileLock` and UTC ISO timestamps. No finding.

### Group 3 — Redaction and Secret Leakage

**Reviewed**: cross-references from Group 1 finding 1.8 (already Critical),
plus surveys of `release/publish.py`, `install/installers.py`,
`gateway/platforms/*.py`, `llm/http.py`, `eval/trajectories.py`.

#### 3.1 [Critical · Security] Duplicate redaction implementations, only one is complete

**See finding 1.8** — the shared `_redact` in `agent/events.py` does not
inspect string values, while `mcp/credentials.py:redact_sensitive` does.
Every consumer of `events._redact` (observability, trajectories, event
bus JSONL, background job runner) is under-redacted.

#### 3.2 [Medium · Security] Trajectory `redact_text_fields` only scans top-level dict

**Location**: `eval/trajectories.py:98-107`

`_redact_with_text(payload, text_fields)` first runs `_redact` recursively
(dict/list) but only sweeps the `text_fields` set against the **top-level
keys of the returned dict**. Nested `outputs.data.text` or
`outputs.results[0].text` remain in cleartext because the loop does not
recurse.

**Failure scenario**: Trajectory step records
`outputs={"data": {"text": "MY PRIVATE DRAFT"}}` with
`redact_text_fields=("text",)`. Export writes the private draft
verbatim. The Task 182 companion test only covers the flat case.

**Fix direction**: Extend `_redact_with_text` (or replace it with a
walker) to recurse into nested dicts/lists and replace `text_fields`
matches at every depth.

#### 3.3 [Note] `release/publish.py` and `install/installers.py` redaction is sound

Token / signing credential are routed only via `runner.env` and
`credential_reader` — steps, summary, stdout are clean per Task 183/185
tests. Finding 1.8 does not apply here because the tests cover string
value paths directly.

#### 3.4 [Low · Maintainability] `release.publish._redact_argv` name is misleading

**Location**: `release/publish.py:218-219`

`_redact_argv(argv) -> " ".join(argv)` — the function does not redact.
Currently safe because twine reads secrets from env, but a future
maintainer might reuse it thinking it redacts.

**Fix direction**: Rename to `_format_argv` or implement actual argv
redaction that strips known secret-looking substrings.

### Group 4 — Contract vs Degraded Reality

**Reviewed**: `mcp/client.py`, `environments/{docker,modal,daytona,ssh,singularity}.py`,
`gateway/platforms/*.py`.

#### 4.1 [High · Architecture] MCP placeholder transport silently returns "not configured" instead of failing loud

**Location**: `mcp/client.py:130-158` `StdioMCPTransport`, and the
`_transport_for()` factory at `client.py:245-250`

The placeholder returns `{"ok": False, "error": "stdio execution
adapter not configured"}` — but callers that pattern-match on
`{"ok": False}` alone treat this like any other tool failure and
retry / log / degrade. There is no distinguished "not-implemented"
signal.

Combined with finding 1.6 (policy not consulted by client), a naive
production wiring will look green during dev (StaticMCPTransport
handles fixtures) and silently fail every real call in prod, all with
generic "tool failed" telemetry.

**Fix direction**: Raise `ConfigurationError("stdio MCP transport is a
placeholder; wire a real transport before production")` on `.start()`
unless an env flag `PF_AGENT_ALLOW_PLACEHOLDER_MCP=1` is set. This
forces the wiring gap to be visible.

#### 4.2 [High · Architecture] Gateway platform adapters return `delivered=True` from a fake transport

**Location**: `gateway/platforms/telegram.py:59-68`, similar patterns
across discord/slack/signal/email adapters

`TelegramGatewayAdapter.send` returns `SendResult(delivered=True,
retryable=False, message_ids=["telegram-<n>"], …)` **without ever
calling Telegram**. If the operator does not swap the adapter for a
real transport, the app silently claims delivery. There is no
production/dev flag.

**Fix direction**: Add a required constructor flag
`allow_fake_transport: bool = False` — `send/edit` refuse to return
`delivered=True` unless the flag is set or a real client is wired.
Document that production wiring must pass a real `_client` argument.

#### 4.3 [High · Architecture] `environments/*` backends emit dry-run plans regardless of `dry_run` flag

**Location**: `environments/docker.py:26-57`, plus modal/daytona/ssh/
singularity siblings

`DockerExecutionBackend.check(dry_run=True)` returns a plan (fine), but
`.check(dry_run=False)` still just returns a plan with `dry_run=False`
in it — there is no branch that actually invokes `docker run`. There is
no docstring warning; the class name says "backend" not "planner".

**Fix direction**: Rename these classes to `*BackendPlanner` (rename
also propagates through Task 162–168 CLI wiring) OR add a
`NotImplementedError` at construction when `dry_run=False` unless a
real command runner is injected. Either way, close the "looks like a
backend, is a planner" gap.

### Group 5 — CLI Robustness

Deferred to per-command spot check (partial coverage; the 6189-line
`cli.py` is too large to fully audit in this pass).

#### 5.1 [Note] `cli.py` correctly uses lazy imports (confirmed by Explore subagent)

Top of file imports argparse, json, os, sys, pathlib, yaml plus local
`__version__`, `errors`, `reports` — nothing heavy. Handler functions
import their subsystems inside the function body. `pf-agent --help`
does not force-load the full package. Positive finding.

#### 5.2 [Low · Robustness] `_offline_gate` still needs a runtime check when placeholders leak

**Location**: `cli.py:5888` `_offline_gate`

Related to findings 4.1/4.2/4.3: even with `--offline` unset, a machine
without a real MCP / gateway / execution backend transport will
silently return "delivered=True" or "ok" placeholder results. The
`--offline` flag is not the right axis; the axis is "real transport
wired vs not". Consider a `pf-agent doctor --section wiring` that
reports for each subsystem which transport is currently bound.

_(cli.py bare-except sweep and `--format` conflicts not fully audited
in this pass; recommend a dedicated CLI review card if this pass leaves
you unsatisfied.)_

### Group 6 — Provider Layer

Deferred to spot check. `llm/http.py` already reviewed at line 49
(UrllibTransport with try/except OSError + timeout — sound). Two
observations from Group 1:

#### 6.1 [Note] `llm/http.py` UrllibTransport is production-ready

Uses stdlib `urllib.request`, propagates timeout, wraps `HttpTimeout`.
No token logging observed in code paths inspected. Interacts safely
with `FakeHttpTransport`.

_(No new Critical/High finding recorded for Group 6 in this pass;
recommend a dedicated provider review card if you want deeper coverage
of the 4828-line `llm/` package.)_

### Group 7 — Cross-Module and Global Issues

**Reviewed via Explore subagent** (full report captured below).

#### 7.1 [Note] Architecture is sound

- **Circular imports**: none at package boundaries (safe intra-`agent`↔`chat` edge
  through `chat.transcript` leaf).
- **Layering violations**: none found. Low/mid/high layers respect direction.
- **Implicit globals / mutable defaults**: none found. Module-level constants
  are `frozenset`, compiled regex, or immutable dicts.
- **`from __future__ import annotations` coverage**: 88 % (221/250 files); the
  29 uncovered files are `__init__.py` re-exports plus `agent/modes.py` and
  `errors.py`. No fix needed.
- **`cli.py` import weight**: minimal top-of-file imports; handlers lazy-load.
  `pf-agent --help` does not load the full package.
- **`agent/` internal coupling**: clean one-way flow —
  `types/tools/modes → permissions → sandbox/safety/profiles → kernel → loop`.
- **`__init__.py` fatness**: barrel re-exports only, no DB / HTTP / provider
  eager instantiation.

**Explore subagent's actionable items**:
1. Add `from __future__ import annotations` to `agent/modes.py`, `errors.py`
   for consistency.
2. Document the intentional `agent ↔ chat.transcript` cycle to prevent
   accidental tightening.

## Subagent Reports

### Independent Review of Tasks 181–185

_Pending — code-reviewer subagent running._

### Cross-Module Coupling and Circular Imports

_Pending — Explore subagent running._

## Follow-up Cards Suggested

Recommend opening these as hotfix cards **before** Task 186–195. They fix
architectural gaps that new user-facing surfaces will otherwise expose.

- **Task 196** — Wire the middleware chain into the runtime
  (finding **1.5**). Add integration test proving `tool_request` middleware
  fires when a tool is dispatched through the kernel. Also gates finding
  **1.7** because a wired middleware could otherwise weaponize the empty-`old`
  bug.
- **Task 197** — Enforce MCP policy in `MCPClient.call_tool`
  (finding **1.6**). Accept optional `policy` + `approval_gate` in
  `MCPClient.__init__`; block execution when either denies.
- **Task 198** — Unify redaction (finding **1.8** + **3.1**). Move
  `redact_sensitive` from `mcp/credentials.py` into `agent/events.py`, expand
  `_SENSITIVE_KEY_PARTS` to include `bearer, cookie, refresh_token,
  client_secret, private_key, session_token, credential`, deprecate the
  duplicate. Also fix trajectory nested-field redaction (**3.2**).
- **Task 199** — Harden `fs.edit` and `ToolRegistry` (findings **1.7**, **1.9**).
  Refuse empty `old`; either wire real callables into `default_tool_registry`
  or mark stubs `enabled=False`.
- **Task 200** — Enforce `ExecutionGuard` real timeout (finding **1.1**).
  Wrap `func()` in `ThreadPoolExecutor.submit().result(timeout=…)` with
  cancellation; keep `sleep_fn` seam for tests.
- **Task 201** — Fix `MemoryStore` cross-thread + `IdempotencyStore` atomicity
  (findings **2.1**, **2.2**). Move to `check_same_thread=False` guarded by
  `FileLock`; atomic tmp-file + `os.replace` for cron nonces.
- **Task 202** — Loud placeholders (findings **4.1**, **4.2**, **4.3**).
  Add `pf-agent doctor --section wiring` that reports which transport is
  currently bound for each subsystem. Placeholders emit a distinguished error
  or refuse to `start()` unless an explicit `allow_placeholder` flag is set.
- **Task 203** — Refine `InjectionGuard` Chinese regex (finding **1.2**);
  require a dotted tool token to co-occur before flagging.

Order: **196 → 197 → 198** are the highest-value trio (they close the
biggest architectural gaps together). Then any of **199–203** in parallel;
they touch independent modules.

## Coverage Ledger

**Fully reviewed**:

- `agent/permissions.py`, `agent/safety.py`, `agent/sandbox.py`,
  `agent/execution_guard.py`, `agent/tools.py`, `agent/middleware.py`,
  `agent/observability.py`, `agent/events.py`
- `mcp/policy.py`, `mcp/approval.py`, `mcp/credentials.py`, `mcp/client.py`
  (transport section)
- `concurrency.py`, `memory/store.py`, `workflow/state.py` (top),
  `cron/core.py`
- `release/publish.py`, `install/binary_build.py`, `install/installers.py`
  (via code-reviewer subagent, cross-verified)
- `eval/trajectories.py` (via code-reviewer subagent, plus finding 3.2 that
  subagent missed)
- Whole-repo import graph & coupling (Explore subagent)

**Spot-checked (not exhaustively audited)**:

- `cli.py` (6189 lines — only imports, `_offline_gate`, and command-group
  fan-out inspected; recommend a dedicated CLI card if depth is needed)
- `llm/http.py` (UrllibTransport sound), rest of `llm/` (fallback,
  certification, streaming) not deep-read this pass
- `gateway/platforms/telegram.py` (representative; other platforms sampled
  by grep only)
- `environments/docker.py` (representative; other backends sampled by grep)

**Not covered this pass**:

- `chat/*` beyond finding session.py grep-check for branch/merge
- `retrieval/*` (embeddings, vector store, hybrid retrieval, RAG eval)
- `plugins/*`, `notifications/*`, `service/*`, `skills/*` (Task 175–178
  code), `tui/*`, `tools/*` (Task 169–174 managed tool gateway)
- `novel/*` (4439 lines of domain code)
- `install/` beyond binary_build / installers
- All `samples/`, `docs/`, `fixtures/`, `configs/` (out of scope)

**Reviewer**: Claude Opus 4.7, single-pass, ~2 hours reading budget.
**Method**: read + grep for reverse-callers + 2 parallel Explore subagents
(one independent 181–185 audit, one coupling map). No dynamic execution.

## Next Actions For You

1. Read the Executive Summary — 5 minutes.
2. Decide which of 196–203 you want opened as full task cards. I can write
   them in the same shape as 186–195 tomorrow.
3. If any Critical/High finding needs deeper reproducer, I can build one on
   request.
