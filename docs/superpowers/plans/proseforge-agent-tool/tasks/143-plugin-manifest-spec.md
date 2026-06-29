# Task 143: Plugin Manifest Spec / 插件 Manifest 规范

## Goal

定义 ProseForge Agent 插件标准格式。

## Architecture Notes

This card belongs to the **Plugin Platform** track. Keep the implementation focused in the existing ProseForge Agent architecture and reuse established CLI, report, config, permission, and persistence patterns where they already exist.

### Source Core Requirements

插件 manifest：

```yaml id="mo61cn"
plugin:
  id: proseforge-plugin-example
  name: Example Plugin
  version: 0.1.0
  description: Example plugin
  entrypoint: plugin.main:register
  permissions:
    - read_project
    - write_artifacts
  dependencies:
    python:
      - pydantic>=2
  compatible:
    proseforge_agent: ">=0.8.0"
```

## Files

- Create or modify implementation files under `src/proseforge_agent/plugins/` as needed for this card.
- Add focused tests in `tests/plugins/test_plugin_manifest_spec.py`.
- Add fixtures under `tests/plugins/fixtures/plugin-manifest-spec/` only when deterministic sample data is needed.
- Update CLI/report wiring only if the source card explicitly requires a command or user-visible surface.

## Interfaces / Contracts

No extra CLI/API surface was specified in the source card. Preserve existing command style and add only the minimum interface required by the goal.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/plugins/test_plugin_manifest_spec.py::test_plugin_manifest_spec_contract`**

```python
def test_plugin_manifest_spec_contract():
    # Replace this scaffold with the concrete assertion from the card goal.
    # The first run must fail because Task 143 production code is not implemented yet.
    raise AssertionError("Task 143 contract not implemented")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/plugins/test_plugin_manifest_spec.py::test_plugin_manifest_spec_contract -q
```

Expected: FAIL because Task 143 production behavior is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement the smallest cohesive change under `src/proseforge_agent/plugins/` that satisfies the source requirements and keeps unrelated subsystems unchanged.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/plugins/test_plugin_manifest_spec.py::test_plugin_manifest_spec_contract -q
```

Expected: PASS with the new Task 143 behavior covered.

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
git add src/proseforge_agent/plugins/ tests/plugins/test_plugin_manifest_spec.py
git commit -m "feat: add plugin manifest spec"
```

## Verification

Source DoD:

插件目录中存在 manifest 后，系统能解析插件元数据。

---

Before closing this card, run:

```powershell
python -m pytest tests/plugins/test_plugin_manifest_spec.py -q
python -m pytest -q
```

## Acceptance

- The behavior described in the source goal is implemented and covered by tests.
- Any command/API/config surface named in the source card works through the existing project conventions.
- The implementation is deterministic in tests and does not require real network/provider credentials unless the card explicitly says so.
- Existing user data, project artifacts, secrets, and config are preserved unless this card explicitly requires a safe migration or backup.

## Commit Boundary

Commit only Task 143 implementation files, tests, and required fixtures:

```powershell
git add src/proseforge_agent/plugins/ tests/plugins/test_plugin_manifest_spec.py
git commit -m "feat: add plugin manifest spec"
```

Do not bundle adjacent task cards into this commit.
