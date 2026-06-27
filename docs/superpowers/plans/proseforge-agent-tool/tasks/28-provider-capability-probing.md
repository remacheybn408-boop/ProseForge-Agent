# Task 28: Provider Capability Probing

## Goal

Measure configured model capabilities through safe offline and opt-in real probes.

## Architecture Notes

Routing uses observed capability evidence rather than static claims alone.

Read before starting:

- ../architecture/02-system-architecture.md
- ../appendices/01-data-contracts.md
- 00-task-index.md

## Files

- Create `src/proseforge_agent/llm/probes.py`
- Create `src/proseforge_agent/llm/capabilities.py`
- Create `tests/test_provider_probes.py`
- Create `tests/fixtures/providers/probe_results.json`

## Interfaces / Contracts

`CapabilityProbeResult` records provider, model, capability, status, latency, usage, checked_at, error, and evidence. Real probes require `--real` or `--real-if-key-present`.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_provider_probes.py::test_fake_provider_text_and_json_probes_record_evidence`**

```python
def test_fake_provider_text_and_json_probes_record_evidence(fake_provider):
    results = CapabilityProber(fake_provider).run(["text", "json_mode"])
    assert {r.capability for r in results} == {"text", "json_mode"}
    assert all(r.evidence for r in results)
```

- [ ] **Step 2: Run the targeted test and confirm failure**

Run:

```powershell
python -m pytest tests/test_provider_probes.py::test_fake_provider_text_and_json_probes_record_evidence -q
```

Expected: FAIL because capability prober is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement probe definitions for text, streaming, JSON, tool calling, long context, reasoning controls, embeddings, safety behavior, offline replay, and real-call guards.

- [ ] **Step 4: Run the targeted test and confirm pass**

Run:

```powershell
python -m pytest tests/test_provider_probes.py::test_fake_provider_text_and_json_probes_record_evidence -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Run integration verification**

Run:

```powershell
python -m pytest tests/test_provider_probes.py -q
pf-agent provider probe --provider fake --write-report
```

Expected: command exits 0 and writes only the artifacts named in this card.

- [ ] **Step 6: Record commit boundary**

```powershell
git add src/proseforge_agent/llm/probes.py tests
git commit -m "feat: add provider capability probing"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Verification

```powershell
python -m pytest tests/test_provider_probes.py -q
pf-agent provider probe --provider fake --write-report
```

## Acceptance

- Real probes never run without explicit real mode.
- Failed probes write a result instead of mutating provider config.
- Capability matrix can be consumed by the fallback router.

## Commit Boundary

Commit after this card passes verification. Do not start the next card with failing tests or unreviewed artifacts from this card.
