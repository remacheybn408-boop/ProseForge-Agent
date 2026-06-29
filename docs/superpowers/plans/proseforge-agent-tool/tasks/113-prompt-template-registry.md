# Task 113: Prompt Template Registry / Prompt 模板注册表

## Goal

集中管理 workflow prompt 模板，不再散落在代码里。

## Architecture Notes

This card belongs to the **Agent Protocol, Prompt, Context, And Audit** track. Keep the implementation focused in the existing ProseForge Agent architecture and reuse established CLI, report, config, permission, and persistence patterns where they already exist.

### Source Core Requirements

管理模板：

* draft chapter
* review chapter
* rewrite
* expand scene
* condense chapter
* title suggestion
* continuity check
* reader review

字段：

* template id
* version
* variables
* required evidence
* provider compatibility
* changelog

命令：

```bash
pf-agent prompt-template list
pf-agent prompt-template validate draft_chapter_v1
```

## Files

- Create or modify implementation files under `src/proseforge_agent/agent/` as needed for this card.
- Add focused tests in `tests/agent/test_prompt_template_registry.py`.
- Add fixtures under `tests/agent/fixtures/prompt-template-registry/` only when deterministic sample data is needed.
- Update CLI/report wiring only if the source card explicitly requires a command or user-visible surface.

## Interfaces / Contracts

No extra CLI/API surface was specified in the source card. Preserve existing command style and add only the minimum interface required by the goal.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/agent/test_prompt_template_registry.py::test_prompt_template_registry_contract`**

```python
def test_prompt_template_registry_contract():
    # Replace this scaffold with the concrete assertion from the card goal.
    # The first run must fail because Task 113 production code is not implemented yet.
    raise AssertionError("Task 113 contract not implemented")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/agent/test_prompt_template_registry.py::test_prompt_template_registry_contract -q
```

Expected: FAIL because Task 113 production behavior is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement the smallest cohesive change under `src/proseforge_agent/agent/` that satisfies the source requirements and keeps unrelated subsystems unchanged.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/agent/test_prompt_template_registry.py::test_prompt_template_registry_contract -q
```

Expected: PASS with the new Task 113 behavior covered.

- [ ] **Step 5: Add companion tests for the source DoD and failure modes**

Cover all command/API/config behaviors named in this card, including non-destructive behavior, no-secret-leak behavior, permission checks, degraded/offline behavior, or deterministic fake-provider behavior when relevant.

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/agent/ -q
```

Expected: subsystem tests pass.

- [ ] **Step 7: Run full repository verification**

```powershell
python -m pytest -q
```

Expected: full suite passes.

- [ ] **Step 8: Record commit boundary**

```powershell
git add src/proseforge_agent/agent/ tests/agent/test_prompt_template_registry.py
git commit -m "feat: add prompt template registry"
```

## Verification

Source DoD:

workflow 调用 prompt 时通过 registry 获取模板，而不是硬编码字符串。

---

Before closing this card, run:

```powershell
python -m pytest tests/agent/test_prompt_template_registry.py -q
python -m pytest -q
```

## Acceptance

- The behavior described in the source goal is implemented and covered by tests.
- Any command/API/config surface named in the source card works through the existing project conventions.
- The implementation is deterministic in tests and does not require real network/provider credentials unless the card explicitly says so.
- Existing user data, project artifacts, secrets, and config are preserved unless this card explicitly requires a safe migration or backup.

## Commit Boundary

Commit only Task 113 implementation files, tests, and required fixtures:

```powershell
git add src/proseforge_agent/agent/ tests/agent/test_prompt_template_registry.py
git commit -m "feat: add prompt template registry"
```

Do not bundle adjacent task cards into this commit.
