# Task 146: Plugin Permission Model / 插件权限模型

## Goal

为插件定义权限声明和运行时权限检查。

## Architecture Notes

This card belongs to the **Plugin Platform** track. Keep the implementation focused in the existing ProseForge Agent architecture and reuse established CLI, report, config, permission, and persistence patterns where they already exist.

### Source Core Requirements

插件调用敏感能力时必须检查权限。

## Files

- Create or modify implementation files under `src/proseforge_agent/plugins/` as needed for this card.
- Add focused tests in `tests/plugins/test_plugin_permission_model.py`.
- Add fixtures under `tests/plugins/fixtures/plugin-permission-model/` only when deterministic sample data is needed.
- Update CLI/report wiring only if the source card explicitly requires a command or user-visible surface.

## Interfaces / Contracts

### Source 权限类型

```text id="0jkwtd"
read_project
write_project
read_memory
write_memory
read_bible
write_bible
read_files
write_files
network_access
provider_call
mcp_access
secrets_access
shell_access
```

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/plugins/test_plugin_permission_model.py::test_plugin_permission_model_contract`**

```python
def test_plugin_permission_model_contract():
    # Replace this scaffold with the concrete assertion from the card goal.
    # The first run must fail because Task 146 production code is not implemented yet.
    raise AssertionError("Task 146 contract not implemented")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/plugins/test_plugin_permission_model.py::test_plugin_permission_model_contract -q
```

Expected: FAIL because Task 146 production behavior is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement the smallest cohesive change under `src/proseforge_agent/plugins/` that satisfies the source requirements and keeps unrelated subsystems unchanged.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/plugins/test_plugin_permission_model.py::test_plugin_permission_model_contract -q
```

Expected: PASS with the new Task 146 behavior covered.

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
git add src/proseforge_agent/plugins/ tests/plugins/test_plugin_permission_model.py
git commit -m "feat: add plugin permission model"
```

## Verification

Source DoD:

未声明 `write_project` 的插件不能修改项目文件。

---

Before closing this card, run:

```powershell
python -m pytest tests/plugins/test_plugin_permission_model.py -q
python -m pytest -q
```

## Acceptance

- The behavior described in the source goal is implemented and covered by tests.
- Any command/API/config surface named in the source card works through the existing project conventions.
- The implementation is deterministic in tests and does not require real network/provider credentials unless the card explicitly says so.
- Existing user data, project artifacts, secrets, and config are preserved unless this card explicitly requires a safe migration or backup.

## Commit Boundary

Commit only Task 146 implementation files, tests, and required fixtures:

```powershell
git add src/proseforge_agent/plugins/ tests/plugins/test_plugin_permission_model.py
git commit -m "feat: add plugin permission model"
```

Do not bundle adjacent task cards into this commit.
