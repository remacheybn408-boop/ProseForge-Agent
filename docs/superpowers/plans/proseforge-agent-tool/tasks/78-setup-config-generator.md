# Task 78: Setup Config Generator / 智能配置生成器

## Goal

让 setup 自动生成可直接使用的 `config.yaml`，并保证不泄露 API Key。

## Architecture Notes

This card belongs to the **Setup Completion** track. Keep the implementation focused in the existing ProseForge Agent architecture and reuse established CLI, report, config, permission, and persistence patterns where they already exist.

### Source Core Requirements

生成：

```text
~/.proseforge-agent/config.yaml
~/.proseforge-agent/.env
~/.proseforge-agent/workspace/
```

配置示例：

```yaml
agent:
  profile: default
  language: zh-CN
  system_prompt_template: professional_novel_editor

llm:
  default_provider: deepseek
  fallback_provider: fake
  providers:
    fake:
      enabled: true
      configured: true
      model: fake-local
    deepseek:
      enabled: true
      configured: true
      api_key_ref: "keychain://proseforge-agent/deepseek"
      model: deepseek-chat

paths:
  workspace_root: "~/.proseforge-agent/workspace"

setup:
  completed: true
  mode: quick
```

禁止真实 key 明文写入 config。

## Files

- Create or modify implementation files under `src/proseforge_agent/setup/` as needed for this card.
- Add focused tests in `tests/setup/test_setup_config_generator.py`.
- Add fixtures under `tests/setup/fixtures/setup-config-generator/` only when deterministic sample data is needed.
- Update CLI/report wiring only if the source card explicitly requires a command or user-visible surface.

## Interfaces / Contracts

No extra CLI/API surface was specified in the source card. Preserve existing command style and add only the minimum interface required by the goal.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/setup/test_setup_config_generator.py::test_setup_config_generator_contract`**

```python
def test_setup_config_generator_contract():
    # Replace this scaffold with the concrete assertion from the card goal.
    # The first run must fail because Task 78 production code is not implemented yet.
    raise AssertionError("Task 78 contract not implemented")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/setup/test_setup_config_generator.py::test_setup_config_generator_contract -q
```

Expected: FAIL because Task 78 production behavior is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement the smallest cohesive change under `src/proseforge_agent/setup/` that satisfies the source requirements and keeps unrelated subsystems unchanged.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/setup/test_setup_config_generator.py::test_setup_config_generator_contract -q
```

Expected: PASS with the new Task 78 behavior covered.

- [ ] **Step 5: Add companion tests for the source DoD and failure modes**

Cover all command/API/config behaviors named in this card, including non-destructive behavior, no-secret-leak behavior, permission checks, degraded/offline behavior, or deterministic fake-provider behavior when relevant.

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/setup/ -q
```

Expected: subsystem tests pass.

- [ ] **Step 7: Run full repository verification**

```powershell
python -m pytest -q
```

Expected: full suite passes.

- [ ] **Step 8: Record commit boundary**

```powershell
git add src/proseforge_agent/setup/ tests/setup/test_setup_config_generator.py
git commit -m "feat: add setup config generator"
```

## Verification

Source DoD:

```bash
pf-agent setup --quick
pf-agent setup --print-config
```

输出配置摘要，但不得显示真实 API Key。

---

Before closing this card, run:

```powershell
python -m pytest tests/setup/test_setup_config_generator.py -q
python -m pytest -q
```

## Acceptance

- The behavior described in the source goal is implemented and covered by tests.
- Any command/API/config surface named in the source card works through the existing project conventions.
- The implementation is deterministic in tests and does not require real network/provider credentials unless the card explicitly says so.
- Existing user data, project artifacts, secrets, and config are preserved unless this card explicitly requires a safe migration or backup.

## Commit Boundary

Commit only Task 78 implementation files, tests, and required fixtures:

```powershell
git add src/proseforge_agent/setup/ tests/setup/test_setup_config_generator.py
git commit -m "feat: add setup config generator"
```

Do not bundle adjacent task cards into this commit.
