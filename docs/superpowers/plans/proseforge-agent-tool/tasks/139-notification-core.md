# Task 139: Notification Core / 通知核心

## Goal

建立统一通知系统，让后台任务、长任务、失败事件可以通知用户。

## Architecture Notes

This card belongs to the **Notifications And Jobs** track. Keep the implementation focused in the existing ProseForge Agent architecture and reuse established CLI, report, config, permission, and persistence patterns where they already exist.

### Source Core Requirements

通知事件：

* job completed
* job failed
* backup completed
* export completed
* provider degraded
* approval required
* foreshadow overdue
* plot thread stale

内部接口：

```python id="9243q2"
NotificationEvent
NotificationChannel
NotificationDispatcher
```

## Files

- Create or modify implementation files under `src/proseforge_agent/notifications/` as needed for this card.
- Add focused tests in `tests/notifications/test_notification_core.py`.
- Add fixtures under `tests/notifications/fixtures/notification-core/` only when deterministic sample data is needed.
- Update CLI/report wiring only if the source card explicitly requires a command or user-visible surface.

## Interfaces / Contracts

### Source 命令

```bash id="yrr0av"
pf-agent notifications list
pf-agent notifications test
```

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/notifications/test_notification_core.py::test_notification_core_contract`**

```python
def test_notification_core_contract():
    # Replace this scaffold with the concrete assertion from the card goal.
    # The first run must fail because Task 139 production code is not implemented yet.
    raise AssertionError("Task 139 contract not implemented")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/notifications/test_notification_core.py::test_notification_core_contract -q
```

Expected: FAIL because Task 139 production behavior is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement the smallest cohesive change under `src/proseforge_agent/notifications/` that satisfies the source requirements and keeps unrelated subsystems unchanged.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/notifications/test_notification_core.py::test_notification_core_contract -q
```

Expected: PASS with the new Task 139 behavior covered.

- [ ] **Step 5: Add companion tests for the source DoD and failure modes**

Cover all command/API/config behaviors named in this card, including non-destructive behavior, no-secret-leak behavior, permission checks, degraded/offline behavior, or deterministic fake-provider behavior when relevant.

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/notifications/ -q
```

Expected: subsystem tests pass.

- [ ] **Step 7: Run full repository verification**

```powershell
python -m pytest -q
```

Expected: full suite passes.

- [ ] **Step 8: Record commit boundary**

```powershell
git add src/proseforge_agent/notifications/ tests/notifications/test_notification_core.py
git commit -m "feat: add notification core"
```

## Verification

Source DoD:

后台任务完成后能生成通知事件，并写入通知中心。

---

Before closing this card, run:

```powershell
python -m pytest tests/notifications/test_notification_core.py -q
python -m pytest -q
```

## Acceptance

- The behavior described in the source goal is implemented and covered by tests.
- Any command/API/config surface named in the source card works through the existing project conventions.
- The implementation is deterministic in tests and does not require real network/provider credentials unless the card explicitly says so.
- Existing user data, project artifacts, secrets, and config are preserved unless this card explicitly requires a safe migration or backup.

## Commit Boundary

Commit only Task 139 implementation files, tests, and required fixtures:

```powershell
git add src/proseforge_agent/notifications/ tests/notifications/test_notification_core.py
git commit -m "feat: add notification core"
```

Do not bundle adjacent task cards into this commit.
