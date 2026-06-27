# Task 38: Chat Memory And User Preferences

## Goal

Extract durable preferences and project decisions from chat into reviewable memory candidates.

## Agent Product Requirement

Chat should remember useful preferences without silently changing canon.

## Architecture Notes

`ChatMemoryExtractor` reads a chat turn (or a short window of turns) and emits memory *candidates*. It never writes accepted canon. Two scopes exist: global user preferences (language, default chapter length, preferred providers) and project candidates (facts, decisions, contradictions, open questions). Candidates land in the same review queue used by chapter extraction (Task 08); acceptance is a separate human/kernel step. The extractor calls no provider directly except through an injected classifier hook, and writes candidate records as JSONL.

Read before starting:

- ../architecture/02-system-architecture.md
- ../architecture/08-agent-runtime-and-chat.md (Chat Memory section)
- 00-task-index.md

## Files

- Create `src/proseforge_agent/chat/memory.py`
- Create `tests/test_chat_memory_preferences.py`
- Create `tests/fixtures/chat-memory-and-user-preferences/turns.jsonl`

## Interfaces / Contracts

- `ChatMemoryExtractor().extract(text: str, scope: str, project_slug: str | None = None) -> list[MemoryCandidate]`.
- `MemoryCandidate` fields: `scope` (`global` | `project`), `kind` (`preference` | `fact` | `decision` | `contradiction` | `open_question`), `content`, `confidence`, `source` (`chat`), `status` (`candidate`).
- Global preferences and project candidates use different review queues and are never auto-accepted.
- `scope="global"` may not produce project canon; `scope="project"` requires a `project_slug`.

## Data Flow

1. Receive chat text and target scope.
2. Classify durable items into preference/fact/decision/contradiction/open-question.
3. Tag each candidate with scope, confidence, and `status="candidate"`.
4. Route global vs project candidates to their respective queues.
5. Append candidate records as JSONL and return them.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_chat_memory_preferences.py::test_chat_preference_becomes_global_preference_candidate`**

```python
def test_chat_preference_becomes_global_preference_candidate():
    candidates = ChatMemoryExtractor().extract(
        "以后默认中文回答，章节长度 2500 字。", scope="global"
    )
    assert candidates
    pref = candidates[0]
    assert pref.scope == "global"
    assert pref.kind == "preference"
    assert pref.status == "candidate"
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/test_chat_memory_preferences.py::test_chat_preference_becomes_global_preference_candidate -q
```

Expected: FAIL because `ChatMemoryExtractor` and `MemoryCandidate` are missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement `ChatMemoryExtractor`, `MemoryCandidate`, scope routing, and JSONL candidate persistence.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/test_chat_memory_preferences.py::test_chat_preference_becomes_global_preference_candidate -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

```text
test_project_scope_requires_project_slug
test_no_candidate_is_marked_accepted
test_contradiction_is_flagged_not_silently_merged
test_global_and_project_candidates_use_separate_queues
test_chinese_preference_text_round_trips_utf8
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_chat_memory_preferences.py -q
pf-agent chat --message "以后默认中文回答" --provider fake --show-memory-candidates
```

Expected: tests pass and the candidate appears in the review queue, not as accepted canon.

- [ ] **Step 7: Record commit boundary**

```powershell
git add src/proseforge_agent/chat/memory.py tests/test_chat_memory_preferences.py tests/fixtures/chat-memory-and-user-preferences
git commit -m "feat: add chat memory preferences"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Cross-Platform Notes

- Candidate content is UTF-8 and round-trips Chinese text.
- Candidate JSONL paths are relative to the workspace or app data directory.
- No machine-specific absolute paths in records or fixtures.

## Failure Modes To Prove

- `scope="project"` without a project slug raises `ConfigurationError`.
- No extracted item is ever written with `status="accepted"`.
- A contradiction is flagged as `kind="contradiction"`, never auto-merged.
- Empty or non-durable text yields zero candidates, not a crash.

## Verification

```powershell
python -m pytest tests/test_chat_memory_preferences.py -q
pf-agent chat --message "以后默认中文回答" --provider fake --show-memory-candidates
```

## Acceptance

- Durable preferences and decisions become reviewable candidates.
- Global and project scopes are kept separate.
- No chat text becomes accepted canon automatically.
- Contradictions are surfaced for review.

## Commit Boundary

Commit only chat memory files and tests after verification passes. Do not change the accepted-canon memory schema here.
