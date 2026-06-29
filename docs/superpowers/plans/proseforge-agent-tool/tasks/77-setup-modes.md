# Task 77: Setup Modes / 多模式 Setup 流程

## Goal

在 Card 76 的 `pf-agent setup` 基础上，补齐 Quick / Full / Minimal 三种模式，让 setup 不再是一条固定流程。

## Architecture Notes

This card belongs to the **Setup Completion** track. Keep the implementation focused in the existing ProseForge Agent architecture and reuse established CLI, report, config, permission, and persistence patterns where they already exist.

### Source Core Requirements

支持：

```bash
pf-agent setup --quick
pf-agent setup --full
pf-agent setup --minimal
pf-agent setup --non-interactive
```

模式说明：

* Quick：普通用户快速配置，优先推荐 DeepSeek / Qwen / GLM / Doubao / OpenAI / Anthropic / Gemini / Fake。
* Full：逐项配置 workspace、provider、model、base_url、key 存储、shell completion、doctor。
* Minimal：只启用 fake provider，不需要 API key，不需要网络，保证零配置跑通。

默认 `pf-agent setup` 进入模式选择：

```text
[1] Quick
[2] Full
[3] Minimal
```

## Files

- Create or modify implementation files under `src/proseforge_agent/setup/` as needed for this card.
- Add focused tests in `tests/setup/test_setup_modes.py`.
- Add fixtures under `tests/setup/fixtures/setup-modes/` only when deterministic sample data is needed.
- Update CLI/report wiring only if the source card explicitly requires a command or user-visible surface.

## Interfaces / Contracts

No extra CLI/API surface was specified in the source card. Preserve existing command style and add only the minimum interface required by the goal.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/setup/test_setup_modes.py::test_setup_modes_contract`**

```python
def test_setup_modes_contract():
    # Replace this scaffold with the concrete assertion from the card goal.
    # The first run must fail because Task 77 production code is not implemented yet.
    raise AssertionError("Task 77 contract not implemented")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/setup/test_setup_modes.py::test_setup_modes_contract -q
```

Expected: FAIL because Task 77 production behavior is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement the smallest cohesive change under `src/proseforge_agent/setup/` that satisfies the source requirements and keeps unrelated subsystems unchanged.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/setup/test_setup_modes.py::test_setup_modes_contract -q
```

Expected: PASS with the new Task 77 behavior covered.

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
git add src/proseforge_agent/setup/ tests/setup/test_setup_modes.py
git commit -m "feat: add setup modes"
```

## Verification

Source DoD:

```bash
pf-agent setup --minimal
pf-agent chat --provider fake --message "hello"
```

必须跑通。

---

Before closing this card, run:

```powershell
python -m pytest tests/setup/test_setup_modes.py -q
python -m pytest -q
```

## Acceptance

- The behavior described in the source goal is implemented and covered by tests.
- Any command/API/config surface named in the source card works through the existing project conventions.
- The implementation is deterministic in tests and does not require real network/provider credentials unless the card explicitly says so.
- Existing user data, project artifacts, secrets, and config are preserved unless this card explicitly requires a safe migration or backup.

## Commit Boundary

Commit only Task 77 implementation files, tests, and required fixtures:

```powershell
git add src/proseforge_agent/setup/ tests/setup/test_setup_modes.py
git commit -m "feat: add setup modes"
```

Do not bundle adjacent task cards into this commit.
