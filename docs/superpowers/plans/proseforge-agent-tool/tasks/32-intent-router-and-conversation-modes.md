# Task 32: Intent Router And Conversation Modes

## Goal

Classify user turns into stable agent intents and support general chat, project chat, workflow chat, operator chat, and creative chat.

## Agent Product Requirement

The agent must understand whether the user wants a normal answer, project context, workflow action, installation help, provider diagnosis, creative brainstorming, memory update, or a clarifying question.

## Architecture Notes

The router returns intent metadata only. It never calls providers, tools, memory, or workflows directly. The Agent Kernel decides execution after permission checks.

Read before starting:

- ../architecture/08-agent-runtime-and-chat.md
- 31-agent-runtime-kernel.md
- 00-task-index.md

## Files

- Create `src/proseforge_agent/agent/intent_router.py`
- Create `src/proseforge_agent/agent/modes.py`
- Create `tests/test_intent_router.py`
- Create `tests/fixtures/agent/intent_cases.yaml`

## Interfaces / Contracts

- `ConversationMode`: `general_chat`, `project_chat`, `workflow_chat`, `operator_chat`, `creative_chat`.
- `IntentName`: `answer_directly`, `retrieve_context`, `update_memory_candidate`, `start_workflow`, `continue_workflow`, `explain_artifact`, `configure_provider`, `diagnose_installation`, `switch_mode`, `ask_clarifying_question`.
- `IntentDecision(name, confidence, reason, required_permission, target_tool, mode_after_turn)`.

## Data Flow

1. Normalize user text and current mode.
2. Match deterministic command-like requests.
3. Match platform/operator phrases.
4. Match workflow and project phrases.
5. Use provider-assisted classification only when deterministic confidence is low.
6. Return one intent, reason, and required permission.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_intent_router.py::test_operator_chat_detects_install_diagnosis`**

```python
def test_operator_chat_detects_install_diagnosis():
    router = IntentRouter()
    decision = router.classify("为什么 provider key 读不到？", mode="operator_chat")
    assert decision.name == "diagnose_installation"
    assert decision.required_permission == "read_only"
    assert "provider" in decision.reason.lower()
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/test_intent_router.py::test_operator_chat_detects_install_diagnosis -q
```

Expected: FAIL because `IntentRouter` and conversation modes are missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement conversation mode enum, intent enum, deterministic phrase rules, confidence values, reason strings, and required permission mapping.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/test_intent_router.py::test_operator_chat_detects_install_diagnosis -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

Required tests:

```text
test_general_chat_answers_without_project_context
test_project_chat_retrieves_context_for_today_question
test_workflow_chat_requires_permission_for_continue
test_creative_chat_creates_memory_candidate_intent
test_switch_mode_from_general_to_project_requires_project_slug
test_ambiguous_write_request_asks_clarifying_question
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_intent_router.py -q
pf-agent chat classify --mode operator_chat --text "provider key 读不到"
```

Expected: command exits 0 and prints intent, confidence, permission, and reason.

## Cross-Platform Notes

- Intent fixture files are UTF-8 YAML.
- Mode and intent names are ASCII-safe for CLI flags.
- Classifier tests must include Chinese and English examples.

## Failure Modes To Prove

- Unknown mode fails before provider calls.
- Ambiguous write request returns `ask_clarifying_question`.
- Low confidence includes a safe fallback reason.

## Verification

```powershell
python -m pytest tests/test_intent_router.py -q
pf-agent chat classify --mode operator_chat --text "provider key 读不到"
```

## Acceptance

- All five conversation modes are represented.
- Router never executes tools.
- Every intent includes required permission.
- Operator chat can diagnose install/provider questions.
- Creative chat can propose memory candidate creation without accepting canon.

## Commit Boundary

Commit router files and intent fixtures only after verification passes.
