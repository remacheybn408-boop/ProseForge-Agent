# Task 128: Cross-session Search / 跨会话搜索

## Goal

支持在所有历史会话中搜索内容。

## Architecture Notes

This card belongs to the **Conversation Lifecycle** track. Keep the implementation focused in the existing ProseForge Agent architecture and reuse established CLI, report, config, permission, and persistence patterns where they already exist.

### Source Core Requirements

搜索范围：

* user messages
* assistant messages
* tool calls
* decisions
* evidence packs
* project references
* approval records

命令：

```bash id="x4a3v4"
pf-agent session search "DeepSeek"
pf-agent session search "第3章" --project demo_novel
```

## Files

- Create or modify implementation files under `src/proseforge_agent/chat/` as needed for this card.
- Add focused tests in `tests/chat/test_cross_session_search.py`.
- Add fixtures under `tests/chat/fixtures/cross-session-search/` only when deterministic sample data is needed.
- Update CLI/report wiring only if the source card explicitly requires a command or user-visible surface.

## Interfaces / Contracts

No extra CLI/API surface was specified in the source card. Preserve existing command style and add only the minimum interface required by the goal.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/chat/test_cross_session_search.py::test_cross_session_search_contract`**

```python
def test_cross_session_search_contract():
    # Replace this scaffold with the concrete assertion from the card goal.
    # The first run must fail because Task 128 production code is not implemented yet.
    raise AssertionError("Task 128 contract not implemented")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/chat/test_cross_session_search.py::test_cross_session_search_contract -q
```

Expected: FAIL because Task 128 production behavior is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement the smallest cohesive change under `src/proseforge_agent/chat/` that satisfies the source requirements and keeps unrelated subsystems unchanged.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/chat/test_cross_session_search.py::test_cross_session_search_contract -q
```

Expected: PASS with the new Task 128 behavior covered.

- [ ] **Step 5: Add companion tests for the source DoD and failure modes**

Cover all command/API/config behaviors named in this card, including non-destructive behavior, no-secret-leak behavior, permission checks, degraded/offline behavior, or deterministic fake-provider behavior when relevant.

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/chat/ -q
```

Expected: subsystem tests pass.

- [ ] **Step 7: Run full repository verification**

```powershell
python -m pytest -q
```

Expected: full suite passes.

- [ ] **Step 8: Record commit boundary**

```powershell
git add src/proseforge_agent/chat/ tests/chat/test_cross_session_search.py
git commit -m "feat: add cross session search"
```

## Verification

Source DoD:

能找到历史会话中提过的某个章节或 provider 配置。

---

Before closing this card, run:

```powershell
python -m pytest tests/chat/test_cross_session_search.py -q
python -m pytest -q
```

## Acceptance

- The behavior described in the source goal is implemented and covered by tests.
- Any command/API/config surface named in the source card works through the existing project conventions.
- The implementation is deterministic in tests and does not require real network/provider credentials unless the card explicitly says so.
- Existing user data, project artifacts, secrets, and config are preserved unless this card explicitly requires a safe migration or backup.

## Commit Boundary

Commit only Task 128 implementation files, tests, and required fixtures:

```powershell
git add src/proseforge_agent/chat/ tests/chat/test_cross_session_search.py
git commit -m "feat: add cross session search"
```

Do not bundle adjacent task cards into this commit.
