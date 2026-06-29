# Task 109: Structured Function Calling / 结构化工具调用协议

## Goal

实现跨 provider 的工具调用协议层，让 Tool Registry 真正可用。

## Architecture Notes

This card belongs to the **Agent Protocol, Prompt, Context, And Audit** track. Keep the implementation focused in the existing ProseForge Agent architecture and reuse established CLI, report, config, permission, and persistence patterns where they already exist.

### Source Core Requirements

统一适配：

* OpenAI tools
* Anthropic tool_use
* Gemini functionDeclaration
* Fake provider tool call

能力：

* tool schema 转换
* tool call parsing
* JSON schema validation
* tool result injection
* multi-step tool call loop

## Files

- Create or modify implementation files under `src/proseforge_agent/agent/` as needed for this card.
- Add focused tests in `tests/agent/test_structured_function_calling.py`.
- Add fixtures under `tests/agent/fixtures/structured-function-calling/` only when deterministic sample data is needed.
- Update CLI/report wiring only if the source card explicitly requires a command or user-visible surface.

## Interfaces / Contracts

### Source 命令/API

内部 API：

```python
ToolCall
ToolResult
ToolCallParser
ProviderToolAdapter
```

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/agent/test_structured_function_calling.py::test_structured_function_calling_contract`**

```python
def test_structured_function_calling_contract():
    # Replace this scaffold with the concrete assertion from the card goal.
    # The first run must fail because Task 109 production code is not implemented yet.
    raise AssertionError("Task 109 contract not implemented")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/agent/test_structured_function_calling.py::test_structured_function_calling_contract -q
```

Expected: FAIL because Task 109 production behavior is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement the smallest cohesive change under `src/proseforge_agent/agent/` that satisfies the source requirements and keeps unrelated subsystems unchanged.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/agent/test_structured_function_calling.py::test_structured_function_calling_contract -q
```

Expected: PASS with the new Task 109 behavior covered.

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
git add src/proseforge_agent/agent/ tests/agent/test_structured_function_calling.py
git commit -m "feat: add structured function calling"
```

## Verification

Source DoD:

同一个 registered tool 能被不同 provider 调用，并把结果注入 message history。

---

Before closing this card, run:

```powershell
python -m pytest tests/agent/test_structured_function_calling.py -q
python -m pytest -q
```

## Acceptance

- The behavior described in the source goal is implemented and covered by tests.
- Any command/API/config surface named in the source card works through the existing project conventions.
- The implementation is deterministic in tests and does not require real network/provider credentials unless the card explicitly says so.
- Existing user data, project artifacts, secrets, and config are preserved unless this card explicitly requires a safe migration or backup.

## Commit Boundary

Commit only Task 109 implementation files, tests, and required fixtures:

```powershell
git add src/proseforge_agent/agent/ tests/agent/test_structured_function_calling.py
git commit -m "feat: add structured function calling"
```

Do not bundle adjacent task cards into this commit.
