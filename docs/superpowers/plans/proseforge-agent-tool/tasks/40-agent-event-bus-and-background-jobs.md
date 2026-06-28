# Task 40: Agent Event Bus And Background Jobs

## Goal

Record agent events and run safe background jobs such as memory indexing, provider refresh, and report generation.

## Agent Product Requirement

Long-running agent work needs traceability and background execution without hiding failures.

## Architecture Notes

The event bus is the shared trace sink for the Agent Kernel (Task 31), chat, and workflow runs. Every turn and job emits append-only JSONL events. The background job runner executes only allow-listed jobs (memory indexing, provider refresh, report generation); a failed job records a failure event and surfaces it, never swallowing the error. Payloads are redacted so no secret values are written. The bus does not call providers itself; jobs call subsystems through injected interfaces.

Read before starting:

- ../architecture/02-system-architecture.md
- ../architecture/08-agent-runtime-and-chat.md (Agent Kernel, Event Bus)
- 00-task-index.md

## Files

- Create `src/proseforge_agent/agent/events.py`
- Create `tests/test_agent_events_jobs.py`
- Create `tests/fixtures/agent-event-bus-and-background-jobs/events_seed.jsonl`

## Interfaces / Contracts

- `EventBus(root).emit(event: Event) -> EventRecord` appends one JSONL line.
- `Event` / `EventRecord` fields: `trace_id`, `type`, `timestamp`, `severity` (`info` | `warning` | `error`), `subject`, `payload` (redacted dict).
- `BackgroundJobRunner(bus).run(job_name, **kwargs) -> JobResult`; `job_name` must be in the allow-list or it raises `ConfigurationError`.
- A failed job returns `JobResult(status="failed", ...)` and emits an `error` event; it never raises silently or marks itself succeeded.

## Data Flow

1. A caller (kernel turn, chat, workflow) creates an `Event` with a trace id.
2. The bus redacts the payload and appends a JSONL record.
3. A background job is requested by allow-listed name.
4. The runner executes the job through injected subsystem interfaces.
5. The runner emits a completion or failure event and returns a `JobResult`.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_agent_events_jobs.py::test_event_bus_appends_jsonl_record_with_trace_id`**

```python
def test_event_bus_appends_jsonl_record_with_trace_id(tmp_path):
    bus = EventBus(tmp_path)
    record = bus.emit(Event(type="chat.turn", trace_id="t1", subject="hello"))
    assert record.trace_id == "t1"
    assert record.type == "chat.turn"
    lines = (tmp_path / "events.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/test_agent_events_jobs.py::test_event_bus_appends_jsonl_record_with_trace_id -q
```

Expected: FAIL because `EventBus`, `Event`, and `EventRecord` are missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement `EventBus`, `Event`, `EventRecord`, payload redaction, and JSONL append.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/test_agent_events_jobs.py::test_event_bus_appends_jsonl_record_with_trace_id -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

```text
test_failed_background_job_emits_error_event_and_returns_failed
test_unknown_job_name_raises_configuration_error
test_event_payload_redacts_secret_keys
test_events_are_append_only_across_multiple_emits
test_event_subject_round_trips_utf8_chinese_text
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_agent_events_jobs.py -q
pf-agent jobs run memory-index --provider fake --dry-run
```

Expected: tests pass and the job runner reports the job outcome and the events it wrote.

- [ ] **Step 7: Record commit boundary**

```powershell
git add src/proseforge_agent/agent/events.py tests/test_agent_events_jobs.py tests/fixtures/agent-event-bus-and-background-jobs
git commit -m "feat: add agent event bus"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Cross-Platform Notes

- Event subjects and payloads are UTF-8 and round-trip Chinese text.
- Event file paths are relative to the workspace or app data directory.
- Append behavior works on Windows, macOS, and Linux file systems.

## Failure Modes To Prove

- A failed job emits an `error` event and returns `status="failed"`, never silent success.
- Unknown job name raises `ConfigurationError`.
- Secret-looking payload keys are redacted before write.
- Concurrent emits do not corrupt the JSONL file (append-only).

## Verification

```powershell
python -m pytest tests/test_agent_events_jobs.py -q
pf-agent jobs run memory-index --provider fake --dry-run
```

## Acceptance

- Every agent turn and job can emit a traceable event.
- Background jobs run only from the allow-list.
- Failures are recorded and surfaced, not hidden.
- No secret values appear in event records.

## Commit Boundary

Commit only event bus files and tests after verification passes. Do not add new provider or workflow behavior here.
