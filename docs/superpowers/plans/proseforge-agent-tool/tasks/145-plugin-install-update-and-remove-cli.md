# Task 145: Plugin Install / Update / Remove CLI

## Goal

提供插件安装、更新、删除命令。

## Architecture Notes

This card belongs to the **Plugin Platform** track. Keep the implementation focused in the existing ProseForge Agent architecture and reuse established CLI, report, config, permission, and persistence patterns where they already exist.

### Source Core Requirements

命令：

```bash id="fk356l"
pf-agent plugin install ./my-plugin
pf-agent plugin install <plugin_id>
pf-agent plugin update <plugin_id>
pf-agent plugin remove <plugin_id>
pf-agent plugin enable <plugin_id>
pf-agent plugin disable <plugin_id>
```

要求：

* 安装前检查 manifest
* 安装前检查权限
* 删除时不删用户数据，除非确认
* 更新前备份旧版本

## Files

- Create or modify implementation files under `src/proseforge_agent/plugins/` as needed for this card.
- Add focused tests in `tests/plugins/test_plugin_install_and_update_and_remove_cli.py`.
- Add fixtures under `tests/plugins/fixtures/plugin-install-and-update-and-remove-cli/` only when deterministic sample data is needed.
- Update CLI/report wiring only if the source card explicitly requires a command or user-visible surface.

## Interfaces / Contracts

No extra CLI/API surface was specified in the source card. Preserve existing command style and add only the minimum interface required by the goal.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/plugins/test_plugin_install_and_update_and_remove_cli.py::test_plugin_install_and_update_and_remove_cli_contract`**

```python
def test_plugin_install_and_update_and_remove_cli_contract():
    # Replace this scaffold with the concrete assertion from the card goal.
    # The first run must fail because Task 145 production code is not implemented yet.
    raise AssertionError("Task 145 contract not implemented")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/plugins/test_plugin_install_and_update_and_remove_cli.py::test_plugin_install_and_update_and_remove_cli_contract -q
```

Expected: FAIL because Task 145 production behavior is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement the smallest cohesive change under `src/proseforge_agent/plugins/` that satisfies the source requirements and keeps unrelated subsystems unchanged.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/plugins/test_plugin_install_and_update_and_remove_cli.py::test_plugin_install_and_update_and_remove_cli_contract -q
```

Expected: PASS with the new Task 145 behavior covered.

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
git add src/proseforge_agent/plugins/ tests/plugins/test_plugin_install_and_update_and_remove_cli.py
git commit -m "feat: add plugin install and update and remove cli"
```

## Verification

Source DoD:

本地插件可以安装、启用、禁用、删除。

---

Before closing this card, run:

```powershell
python -m pytest tests/plugins/test_plugin_install_and_update_and_remove_cli.py -q
python -m pytest -q
```

## Acceptance

- The behavior described in the source goal is implemented and covered by tests.
- Any command/API/config surface named in the source card works through the existing project conventions.
- The implementation is deterministic in tests and does not require real network/provider credentials unless the card explicitly says so.
- Existing user data, project artifacts, secrets, and config are preserved unless this card explicitly requires a safe migration or backup.

## Commit Boundary

Commit only Task 145 implementation files, tests, and required fixtures:

```powershell
git add src/proseforge_agent/plugins/ tests/plugins/test_plugin_install_and_update_and_remove_cli.py
git commit -m "feat: add plugin install and update and remove cli"
```

Do not bundle adjacent task cards into this commit.
