# Task 140: Desktop Notifications / 桌面原生通知

## Goal

支持 Windows / macOS / Linux 桌面通知。

## Architecture Notes

This card belongs to the **Notifications And Jobs** track. Keep the implementation focused in the existing ProseForge Agent architecture and reuse established CLI, report, config, permission, and persistence patterns where they already exist.

### Source Core Requirements

平台：

* Windows toast
* macOS notification
* Linux notify-send

配置：

```yaml id="xcx4mx"
notifications:
  desktop:
    enabled: true
```

命令：

```bash id="qwl4cw"
pf-agent notifications test --desktop
```

## Files

- Create or modify implementation files under `src/proseforge_agent/notifications/` as needed for this card.
- Add focused tests in `tests/notifications/test_desktop_notifications.py`.
- Add fixtures under `tests/notifications/fixtures/desktop-notifications/` only when deterministic sample data is needed.
- Update CLI/report wiring only if the source card explicitly requires a command or user-visible surface.

## Interfaces / Contracts

No extra CLI/API surface was specified in the source card. Preserve existing command style and add only the minimum interface required by the goal.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/notifications/test_desktop_notifications.py::test_desktop_notifications_contract`**

```python
def test_desktop_notifications_contract():
    # Replace this scaffold with the concrete assertion from the card goal.
    # The first run must fail because Task 140 production code is not implemented yet.
    raise AssertionError("Task 140 contract not implemented")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/notifications/test_desktop_notifications.py::test_desktop_notifications_contract -q
```

Expected: FAIL because Task 140 production behavior is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement the smallest cohesive change under `src/proseforge_agent/notifications/` that satisfies the source requirements and keeps unrelated subsystems unchanged.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/notifications/test_desktop_notifications.py::test_desktop_notifications_contract -q
```

Expected: PASS with the new Task 140 behavior covered.

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
git add src/proseforge_agent/notifications/ tests/notifications/test_desktop_notifications.py
git commit -m "feat: add desktop notifications"
```

## Verification

Source DoD:

`pf-agent notifications test --desktop` 能弹出桌面通知或给出不支持原因。

---

Before closing this card, run:

```powershell
python -m pytest tests/notifications/test_desktop_notifications.py -q
python -m pytest -q
```

## Acceptance

- The behavior described in the source goal is implemented and covered by tests.
- Any command/API/config surface named in the source card works through the existing project conventions.
- The implementation is deterministic in tests and does not require real network/provider credentials unless the card explicitly says so.
- Existing user data, project artifacts, secrets, and config are preserved unless this card explicitly requires a safe migration or backup.

## Commit Boundary

Commit only Task 140 implementation files, tests, and required fixtures:

```powershell
git add src/proseforge_agent/notifications/ tests/notifications/test_desktop_notifications.py
git commit -m "feat: add desktop notifications"
```

Do not bundle adjacent task cards into this commit.
