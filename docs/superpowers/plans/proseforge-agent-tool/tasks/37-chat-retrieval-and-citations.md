# Task 37: Chat Retrieval And Citations

## Goal

Let project chat answer with retrieved memory, plan, report, and workflow citations.

## Agent Product Requirement

Project chat must show where its answer came from so the writer can trust it.

## Architecture Notes

`ChatRetrievalResponder` sits between the Agent Kernel (Task 31) and the existing retrieval router (Task 09) / memory store (Task 07). It plans a retrieval intent from a chat question, gathers evidence, calls the provider through the injected gateway, and attaches citations that point back to retrieved source ids. It must not invent canon: every canon-level claim in the answer must map to a retrieved source id. It does not write project canon and does not call providers directly other than through the injected role gateway.

Read before starting:

- ../architecture/02-system-architecture.md
- ../architecture/04-deep-memory-and-retrieval.md
- ../architecture/08-agent-runtime-and-chat.md
- 00-task-index.md

## Files

- Create `src/proseforge_agent/chat/retrieval.py`
- Create `tests/test_chat_retrieval_citations.py`
- Create `tests/fixtures/chat-retrieval-and-citations/memory_seed.json`

## Interfaces / Contracts

- `ChatRetrievalResponder(memory_store, report_store, provider).answer(project: str, question: str) -> ChatAnswer`.
- `ChatAnswer` fields: `text`, `citations` (list of `{source_id, source_type, snippet}`), `used_evidence_ids`, `degraded` (bool).
- Every citation `source_id` must exist in `used_evidence_ids`; no citation may reference an id that was not retrieved.
- When retrieval returns nothing, the answer sets `degraded=True` and states it lacks project evidence instead of fabricating canon.

## Data Flow

1. Build a retrieval intent from the chat question.
2. Query Agent memory and ProseForge-derived sources through the retrieval router.
3. Assemble an evidence pack with stable source ids.
4. Call the provider role with the evidence-grounded prompt.
5. Bind each canon claim in the response to a retrieved source id.
6. Return `ChatAnswer` with citations and the degraded flag.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_chat_retrieval_citations.py::test_project_chat_answer_cites_only_retrieved_sources`**

```python
def test_project_chat_answer_cites_only_retrieved_sources(memory_store, report_store, fake_provider):
    responder = ChatRetrievalResponder(memory_store, report_store, fake_provider)
    answer = responder.answer(project="demo", question="昨天写到哪里了？")
    assert answer.citations
    cited = {c["source_id"] for c in answer.citations}
    assert cited.issubset(set(answer.used_evidence_ids))
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/test_chat_retrieval_citations.py::test_project_chat_answer_cites_only_retrieved_sources -q
```

Expected: FAIL because `ChatRetrievalResponder` and `ChatAnswer` are missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement `ChatRetrievalResponder`, `ChatAnswer`, intent planning, evidence assembly, and citation binding.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/test_chat_retrieval_citations.py::test_project_chat_answer_cites_only_retrieved_sources -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

```text
test_empty_retrieval_sets_degraded_and_avoids_canon_claims
test_citation_source_ids_resolve_to_real_snippets
test_memory_and_report_sources_are_both_citable
test_answer_does_not_cite_unretrieved_ids
test_chinese_question_returns_utf8_citations
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_chat_retrieval_citations.py -q
pf-agent chat --message "昨天写到哪里了？" --project demo --provider fake --show-citations
```

Expected: tests pass and the chat answer prints citations that resolve to retrieved sources.

- [ ] **Step 7: Record commit boundary**

```powershell
git add src/proseforge_agent/chat/retrieval.py tests/test_chat_retrieval_citations.py tests/fixtures/chat-retrieval-and-citations
git commit -m "feat: add chat retrieval citations"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Cross-Platform Notes

- Source ids and snippets are UTF-8 and round-trip Chinese text.
- Snippets never embed absolute file paths; they reference logical source ids.
- Tests run without network or real provider keys (fake provider only).

## Failure Modes To Prove

- Empty retrieval yields `degraded=True` and no fabricated canon claim.
- A citation that references an unretrieved id fails the contract test.
- Provider failure is surfaced with a recovery hint, not a silent empty answer.
- Missing project produces a recovery command, not a stack trace.

## Verification

```powershell
python -m pytest tests/test_chat_retrieval_citations.py -q
pf-agent chat --message "昨天写到哪里了？" --project demo --provider fake --show-citations
```

## Acceptance

- Project chat answers include citations resolvable to retrieved sources.
- No canon claim appears without a backing source id.
- Degraded retrieval is explicit, not hidden.
- The responder reuses the existing retrieval router and memory store.

## Commit Boundary

Commit only chat retrieval files and tests after verification passes. Do not modify the retrieval router or memory store schema here.
