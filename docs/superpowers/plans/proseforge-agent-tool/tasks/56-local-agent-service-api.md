# Task 56: Local Agent Service API

## Goal

Expose an optional local API so future desktop UI, browser UI, and integrations can talk to the same kernel.

## Agent Product Requirement

A complete agent needs a reusable runtime surface beyond the CLI while keeping the CLI first.

## Architecture Notes

`service.api` is a thin local-only HTTP surface over the Agent Kernel (Task 31). It adds no business logic: each route maps to a kernel or store call and returns the kernel's machine-readable result. It binds to loopback by default and requires an explicit opt-in (and permission) to bind elsewhere. This card introduces a new `service/` subpackage (record it in architecture 02). The CLI remains the primary surface; the API is optional.

Read before starting:

- ../architecture/02-system-architecture.md
- ../architecture/08-agent-runtime-and-chat.md (Agent Kernel)
- 00-task-index.md

## Files

- Create `src/proseforge_agent/service/__init__.py`
- Create `src/proseforge_agent/service/api.py`
- Create `tests/test_local_agent_service_api.py`
- Create `tests/fixtures/local-agent-service-api/requests.json`

## Interfaces / Contracts

- `LocalAgentService(kernel, session_store)` exposes `health()`, `chat(payload)`, `sessions()`, `provider_status()`, and `workflow_status(run_id)`.
- `chat(payload)` calls `kernel.run_turn(...)` and returns the serialized `AgentTurnResult`; the service adds no model logic.
- Default bind is `127.0.0.1`; binding to a non-loopback host requires `--allow-remote` and the `system_write` permission.
- All responses are JSON; no secret values are included.

## Data Flow

1. Receive a request on a local-only socket.
2. Map the route to a kernel or store method.
3. Execute through the injected kernel/session store.
4. Serialize the kernel result to JSON.
5. Return the response without adding model logic.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_local_agent_service_api.py::test_chat_route_delegates_to_kernel_run_turn`**

```python
def test_chat_route_delegates_to_kernel_run_turn(fake_kernel):
    service = LocalAgentService(kernel=fake_kernel, session_store=None)
    response = service.chat({"message": "hello", "mode": "general_chat"})
    assert response["text"] == fake_kernel.last_result.text
    assert fake_kernel.run_turn_called is True
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/test_local_agent_service_api.py::test_chat_route_delegates_to_kernel_run_turn -q
```

Expected: FAIL because `LocalAgentService` is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement `LocalAgentService`, the route handlers, loopback binding, and JSON serialization.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/test_local_agent_service_api.py::test_chat_route_delegates_to_kernel_run_turn -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

```text
test_default_bind_is_loopback_only
test_non_loopback_bind_requires_allow_remote_and_permission
test_health_route_returns_version_and_status
test_responses_contain_no_secret_values
test_chat_payload_supports_utf8_chinese_text
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_local_agent_service_api.py -q
pf-agent service start --provider fake --check
```

Expected: tests pass and `service start --check` confirms a loopback-only bind without staying resident.

- [ ] **Step 7: Run cross-platform contract check**

```powershell
python -m pytest tests/test_local_agent_service_api.py -q
```

Expected: PASS on Windows, macOS, and Linux (in-process test client, no real port required).

- [ ] **Step 8: Record commit boundary**

```powershell
git add src/proseforge_agent/service tests/test_local_agent_service_api.py tests/fixtures/local-agent-service-api
git commit -m "feat: add local agent service api"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Cross-Platform Notes

- Tests use an in-process client; no real socket binding is required.
- Default bind is loopback on all platforms.
- Chat payloads round-trip UTF-8 Chinese text.

## Failure Modes To Prove

- Default bind is loopback only.
- Non-loopback bind requires `--allow-remote` and `system_write`.
- Responses never contain secret values.
- The service adds no model logic beyond delegating to the kernel.

## Verification

```powershell
python -m pytest tests/test_local_agent_service_api.py -q
pf-agent service start --provider fake --check
```

## Acceptance

- The same kernel powers CLI and local API.
- Default binding is local-only.
- Routes delegate to kernel/store calls.
- Responses are JSON with no secrets.

## Commit Boundary

Commit only service files and tests after verification passes. Do not add model or workflow logic to the service layer.
