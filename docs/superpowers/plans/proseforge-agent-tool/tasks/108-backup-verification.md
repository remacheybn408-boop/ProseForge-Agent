# Task 108: Backup Verification / 备份验证

## Goal

增强备份能力，不只备份，还要验证能恢复。

## Architecture Notes

This card belongs to the **Writing Quality And Editorial Systems** track. Keep the implementation focused in the existing ProseForge Agent architecture and reuse established CLI, report, config, permission, and persistence patterns where they already exist.

### Source Core Requirements

备份范围：

* workspace
* drafts
* config
* rules
* bible
* timeline
* agent.db
* memory db
* artifact graph

命令：

```bash
pf-agent backup create
pf-agent backup verify backup_001
pf-agent backup restore backup_001 --dry-run
```

要求：

* 备份后自动校验 checksum
* 支持 dry-run restore
* 支持定时备份接口
* 可选远端备份预留接口

## Files

- Create or modify implementation files under `src/proseforge_agent/novel/` as needed for this card.
- Add focused tests in `tests/novel/test_backup_verification.py`.
- Add fixtures under `tests/novel/fixtures/backup-verification/` only when deterministic sample data is needed.
- Update CLI/report wiring only if the source card explicitly requires a command or user-visible surface.

## Interfaces / Contracts

No extra CLI/API surface was specified in the source card. Preserve existing command style and add only the minimum interface required by the goal.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/novel/test_backup_verification.py::test_backup_verification_contract`**

```python
def test_backup_verification_contract():
    # Replace this scaffold with the concrete assertion from the card goal.
    # The first run must fail because Task 108 production code is not implemented yet.
    raise AssertionError("Task 108 contract not implemented")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/novel/test_backup_verification.py::test_backup_verification_contract -q
```

Expected: FAIL because Task 108 production behavior is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement the smallest cohesive change under `src/proseforge_agent/novel/` that satisfies the source requirements and keeps unrelated subsystems unchanged.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/novel/test_backup_verification.py::test_backup_verification_contract -q
```

Expected: PASS with the new Task 108 behavior covered.

- [ ] **Step 5: Add companion tests for the source DoD and failure modes**

Cover all command/API/config behaviors named in this card, including non-destructive behavior, no-secret-leak behavior, permission checks, degraded/offline behavior, or deterministic fake-provider behavior when relevant.

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/novel/ -q
```

Expected: subsystem tests pass.

- [ ] **Step 7: Run full repository verification**

```powershell
python -m pytest -q
```

Expected: full suite passes.

- [ ] **Step 8: Record commit boundary**

```powershell
git add src/proseforge_agent/novel/ tests/novel/test_backup_verification.py
git commit -m "feat: add backup verification"
```

## Verification

Source DoD:

创建备份后能验证，并 dry-run 恢复。

---

Before closing this card, run:

```powershell
python -m pytest tests/novel/test_backup_verification.py -q
python -m pytest -q
```

## Acceptance

- The behavior described in the source goal is implemented and covered by tests.
- Any command/API/config surface named in the source card works through the existing project conventions.
- The implementation is deterministic in tests and does not require real network/provider credentials unless the card explicitly says so.
- Existing user data, project artifacts, secrets, and config are preserved unless this card explicitly requires a safe migration or backup.

## Commit Boundary

Commit only Task 108 implementation files, tests, and required fixtures:

```powershell
git add src/proseforge_agent/novel/ tests/novel/test_backup_verification.py
git commit -m "feat: add backup verification"
```

Do not bundle adjacent task cards into this commit.
