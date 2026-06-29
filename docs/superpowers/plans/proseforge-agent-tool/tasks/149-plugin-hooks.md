# Task 149: Plugin Hooks / 插件生命周期钩子

## Goal

让插件可以扩展 ProseForge Agent 的关键流程。

## Architecture Notes

This card belongs to the **Plugin Platform** track. Keep the implementation focused in the existing ProseForge Agent architecture and reuse established CLI, report, config, permission, and persistence patterns where they already exist.

### Source Core Requirements

插件注册：

```python id="hj4ssw"
def register(plugin_api):
    plugin_api.hooks.on_after_draft(my_handler)
```

## Files

- Create or modify implementation files under `src/proseforge_agent/plugins/` as needed for this card.
- Add focused tests in `tests/plugins/test_plugin_hooks.py`.
- Add fixtures under `tests/plugins/fixtures/plugin-hooks/` only when deterministic sample data is needed.
- Update CLI/report wiring only if the source card explicitly requires a command or user-visible surface.

## Interfaces / Contracts

### Source Hook 类型

```text id="zmgsgf"
on_agent_start
on_project_open
on_before_draft
on_after_draft
on_before_review
on_after_review
on_before_export
on_after_export
on_notification
on_approval_created
```

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/plugins/test_plugin_hooks.py::test_plugin_hooks_contract`**

```python
def test_plugin_hooks_contract():
    # Replace this scaffold with the concrete assertion from the card goal.
    # The first run must fail because Task 149 production code is not implemented yet.
    raise AssertionError("Task 149 contract not implemented")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/plugins/test_plugin_hooks.py::test_plugin_hooks_contract -q
```

Expected: FAIL because Task 149 production behavior is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement the smallest cohesive change under `src/proseforge_agent/plugins/` that satisfies the source requirements and keeps unrelated subsystems unchanged.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/plugins/test_plugin_hooks.py::test_plugin_hooks_contract -q
```

Expected: PASS with the new Task 149 behavior covered.

- [ ] **Step 5: Add companion tests for the source DoD and failure modes**

Cover all command/API/config behaviors named in this card, including non-destructive behavior, no-secret-leak behavior, permission checks, degraded/offline behavior, or deterministic fake-provider behavior when relevant.

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/plugins/ -q
```

Expected: subsystem tests pass.

- [ ] **Step 7: Run full repository verification**

```powershell
python -m pytest -q
```

Expected: full suite passes.

- [ ] **Step 8: Record commit boundary**

```powershell
git add src/proseforge_agent/plugins/ tests/plugins/test_plugin_hooks.py
git commit -m "feat: add plugin hooks"
```

## Verification

Source DoD:

插件能注册 `on_after_export`，在导出完成后收到事件。

---

Before closing this card, run:

```powershell
python -m pytest tests/plugins/test_plugin_hooks.py -q
python -m pytest -q
```

## Acceptance

- The behavior described in the source goal is implemented and covered by tests.
- Any command/API/config surface named in the source card works through the existing project conventions.
- The implementation is deterministic in tests and does not require real network/provider credentials unless the card explicitly says so.
- Existing user data, project artifacts, secrets, and config are preserved unless this card explicitly requires a safe migration or backup.

## Commit Boundary

Commit only Task 149 implementation files, tests, and required fixtures:

```powershell
git add src/proseforge_agent/plugins/ tests/plugins/test_plugin_hooks.py
git commit -m "feat: add plugin hooks"
```

Do not bundle adjacent task cards into this commit.
