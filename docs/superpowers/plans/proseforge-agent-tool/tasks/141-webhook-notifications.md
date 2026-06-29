# Task 141: Webhook Notifications / Webhook 推送

## Goal

支持把通知推送到外部系统，例如飞书、钉钉、企业微信、自定义 webhook。

## Architecture Notes

This card belongs to the **Notifications And Jobs** track. Keep the implementation focused in the existing ProseForge Agent architecture and reuse established CLI, report, config, permission, and persistence patterns where they already exist.

### Source Core Requirements

配置：

```yaml id="da8elv"
notifications:
  webhook:
    enabled: true
    url_ref: "keychain://proseforge-agent/webhook_url"
    events:
      - job_failed
      - approval_required
```

要求：

* webhook URL 不明文打印
* 支持 retry
* 支持 timeout
* 支持签名 secret 预留

## Files

- Create or modify implementation files under `src/proseforge_agent/notifications/` as needed for this card.
- Add focused tests in `tests/notifications/test_webhook_notifications.py`.
- Add fixtures under `tests/notifications/fixtures/webhook-notifications/` only when deterministic sample data is needed.
- Update CLI/report wiring only if the source card explicitly requires a command or user-visible surface.

## Interfaces / Contracts

### Source 命令

```bash id="bsz2w4"
pf-agent notifications test --webhook
```

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/notifications/test_webhook_notifications.py::test_webhook_notifications_contract`**

```python
def test_webhook_notifications_contract():
    # Replace this scaffold with the concrete assertion from the card goal.
    # The first run must fail because Task 141 production code is not implemented yet.
    raise AssertionError("Task 141 contract not implemented")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/notifications/test_webhook_notifications.py::test_webhook_notifications_contract -q
```

Expected: FAIL because Task 141 production behavior is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement the smallest cohesive change under `src/proseforge_agent/notifications/` that satisfies the source requirements and keeps unrelated subsystems unchanged.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/notifications/test_webhook_notifications.py::test_webhook_notifications_contract -q
```

Expected: PASS with the new Task 141 behavior covered.

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
git add src/proseforge_agent/notifications/ tests/notifications/test_webhook_notifications.py
git commit -m "feat: add webhook notifications"
```

## Verification

Source DoD:

任务失败时能推送 webhook，并在失败时记录 retry log。

---

Before closing this card, run:

```powershell
python -m pytest tests/notifications/test_webhook_notifications.py -q
python -m pytest -q
```

## Acceptance

- The behavior described in the source goal is implemented and covered by tests.
- Any command/API/config surface named in the source card works through the existing project conventions.
- The implementation is deterministic in tests and does not require real network/provider credentials unless the card explicitly says so.
- Existing user data, project artifacts, secrets, and config are preserved unless this card explicitly requires a safe migration or backup.

## Commit Boundary

Commit only Task 141 implementation files, tests, and required fixtures:

```powershell
git add src/proseforge_agent/notifications/ tests/notifications/test_webhook_notifications.py
git commit -m "feat: add webhook notifications"
```

Do not bundle adjacent task cards into this commit.
