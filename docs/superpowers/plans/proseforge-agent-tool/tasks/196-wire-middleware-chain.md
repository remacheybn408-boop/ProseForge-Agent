# Task 196: Wire The Middleware Chain Into The Runtime / 中间件链接线

## Goal

Make the `MiddlewareRegistry` (Task 182) actually run. Today
`apply_tool_request` / `apply_tool_execution` / `apply_llm_request` /
`apply_llm_execution` have **zero callers** outside `middleware.py` itself
(`grep` confirms) — registering a middleware has no runtime effect. Wire the
chain into the tool-dispatch path and the provider-call path so a registered,
enabled middleware fires, and prove that a rewritten request is
**re-authorized** before it runs.

## Architecture Notes

Fixes **finding 1.5** (Critical · Architecture) of
`docs/review/core-review-2026-07-01.md`. Related: this card is a **prerequisite
gate for finding 1.7** — an unwired middleware cannot yet weaponize the empty
`old` `fs.edit` bug, but once wired it could, so 199 must land the `_fs_edit`
guard.

The registry already implements the correct semantics
(`src/proseforge_agent/agent/middleware.py`):

- `apply_tool_request(ToolRequest) -> ToolRequest` — ordered, enabled-only,
  fail-open, records `MiddlewareTrace(rewritten=...)`.
- `apply_tool_execution(ToolExecutionContext, base_call) -> ToolResult` —
  `next_call` chain around the real call.
- `apply_llm_request` / `apply_llm_execution` — same for provider calls.

The gap is purely **wiring**: the `AgentKernel` / tool dispatcher and the
provider-call site bypass the registry. The module docstring already states the
contract we must honor: *"Downstream policy MUST re-check any rewritten request
or tool args."*

Design:

1. Give the dispatch path an optional `middleware: MiddlewareRegistry | None`.
   When present, before permission authorization:
   `req = middleware.apply_tool_request(ToolRequest(tool_name, arguments))`.
2. **Re-authorize** using the possibly-rewritten `req.tool_name` +
   `req.arguments` (call `PermissionPolicy.authorize` on the rewritten request,
   never the original).
3. Wrap the actual `ToolRegistry.invoke` inside
   `middleware.apply_tool_execution(ToolExecutionContext(req.tool_name,
   req.arguments), base_call)`.
4. Same pattern for provider calls: `apply_llm_request` before the request is
   sent, `apply_llm_execution` around `provider.chat`.
5. When `middleware is None`, behavior is byte-for-byte the current behavior
   (no registry constructed, no traces).

Read before starting:

- `docs/review/core-review-2026-07-01.md` (finding 1.5, and 1.4/1.7 context)
- 182-middleware-hooks-and-trajectory-datasets.md
- 31-agent-runtime-kernel.md
- `src/proseforge_agent/agent/middleware.py`, `agent/permissions.py`,
  `agent/tools.py`, `agent/kernel.py`

## Files

- Modify the tool-dispatch site (`src/proseforge_agent/agent/kernel.py` and/or
  the dispatcher that calls `PermissionPolicy.authorize` + `ToolRegistry.invoke`)
  to accept and apply an optional `MiddlewareRegistry`.
- Modify the provider-call site to apply `apply_llm_request` /
  `apply_llm_execution`.
- Do NOT change `middleware.py` behavior (it is already correct); only import
  and call it.
- Add tests in `tests/test_middleware_wiring.py`.

## Interfaces / Contracts

- Dispatch entry point gains `middleware: MiddlewareRegistry | None = None`
  (keyword-only, default None → no behavior change).
- A rewritten `tool_request` MUST be re-authorized: if the middleware changes
  `arguments` to something the ceiling forbids, dispatch denies.
- Traces are observable via `middleware.traces()` after a dispatch.
- Fail-open is preserved: a middleware that raises is recorded in
  `middleware.failures()` and the chain continues.

## Data Flow

1. Caller registers + enables a `tool_request` middleware.
2. Kernel dispatches a tool → `apply_tool_request` runs → rewritten request.
3. `PermissionPolicy.authorize(rewritten)` runs (re-check).
4. `apply_tool_execution` wraps `ToolRegistry.invoke`.
5. Result returned; `traces()` shows the middleware fired.

## TDD Steps

- [ ] **Step 1: Write failing test
  `tests/test_middleware_wiring.py::test_tool_request_middleware_fires_on_dispatch`**

```python
def test_tool_request_middleware_fires_on_dispatch():
    registry = MiddlewareRegistry()
    seen = []

    def tag(req):
        seen.append(req.tool_name)
        return req.with_arguments({**req.arguments, "tagged": True})

    registry.register(MIDDLEWARE_KIND_TOOL_REQUEST, "tag", tag, enabled=True)

    kernel = build_kernel(middleware=registry)  # dispatch helper under test
    result = kernel.dispatch_tool("memory.search", {"query": "x"})

    assert seen == ["memory.search"]          # middleware actually ran
    assert any(t.name == "tag" and t.rewritten for t in registry.traces())
```

- [ ] **Step 2: Run the targeted test and confirm failure** (middleware never
  fires today; `seen` stays empty).

- [ ] **Step 3: Wire `apply_tool_request` + re-auth + `apply_tool_execution`
  into the dispatcher, and `apply_llm_*` into the provider-call site.**

- [ ] **Step 4: Run the targeted test and confirm pass.**

- [ ] **Step 5: Companion tests**

```text
test_rewritten_request_is_reauthorized_and_denied_when_ceiling_forbids
test_tool_execution_middleware_wraps_invoke_with_next_call
test_llm_request_middleware_fires_before_provider_call
test_middleware_none_is_byte_for_byte_current_behavior
test_failing_middleware_is_recorded_and_chain_continues
```

- [ ] **Step 6: Subsystem verification**

```powershell
python -m pytest tests/test_middleware_wiring.py tests/test_middleware_hooks_and_trajectory_datasets.py -q
```

- [ ] **Step 7: Full repository verification**

```powershell
python -m pytest -q
```

- [ ] **Step 8: Commit boundary**

```powershell
git add src/proseforge_agent/agent/kernel.py src/proseforge_agent/agent/tools.py tests/test_middleware_wiring.py
git commit -m "fix: wire middleware chain into runtime"
```

## Failure Modes To Prove

- A `tool_request` middleware that escalates `arguments` to a forbidden path is
  denied by the re-authorization step (guards against finding 1.4/1.7).
- A `tool_execution` middleware sees `next_call` and can short-circuit.
- `middleware=None` leaves existing kernel tests unchanged.
- A raising middleware does not crash dispatch.

## Verification

```powershell
python -m pytest tests/test_middleware_wiring.py -q
python -m pytest -q
```

## Acceptance

- Registering + enabling a `tool_request` middleware causes it to fire on the
  next kernel tool dispatch; `traces()` proves it.
- Rewritten requests are re-authorized (a forbidden rewrite is denied).
- All existing 182 middleware-contract tests still pass; full suite green;
  new tests added.

## Commit Boundary

Commit only the wiring at the dispatch/provider sites and the new wiring tests.
Do not change `middleware.py` semantics, and do not bundle the redaction (198)
or `fs.edit` (199) fixes.
