# Task 30: Provider Docs Refresh And Certification

## Goal

Create the provider maintenance loop for docs refresh, shape certification, real smoke, and release gates.

## Architecture Notes

Provider APIs change; certification records make that change visible and auditable.

Read before starting:

- ../architecture/02-system-architecture.md
- ../appendices/01-data-contracts.md
- 00-task-index.md

## Files

- Create `src/proseforge_agent/llm/certification.py`
- Create `src/proseforge_agent/llm/docs_refresh.py`
- Create `tests/test_provider_certification.py`
- Create `tests/fixtures/providers/certification_records/`

## Interfaces / Contracts

`ProviderCertificationRecord` includes provider, family, protocol, model, source_urls, checked_date, shape_status, smoke_status, workflow_status, capability_status, limitations, and next_refresh_due.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_provider_certification.py::test_release_check_fails_when_requested_provider_has_no_shape_certification`**

```python
def test_release_check_fails_when_requested_provider_has_no_shape_certification(tmp_path):
    records = CertificationStore(tmp_path)
    records.write(provider="openai", shape_status="passed", source_urls=["https://example.test/openai"], checked_date="2026-06-27")
    result = ProviderReleaseCheck(records).run(required=["openai", "deepseek"])
    assert result.status == "failed"
    assert "deepseek" in result.missing_providers
```

- [ ] **Step 2: Run the targeted test and confirm failure**

Run:

```powershell
python -m pytest tests/test_provider_certification.py::test_release_check_fails_when_requested_provider_has_no_shape_certification -q
```

Expected: FAIL because certification store and release check are missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement certification schema, source URL validation, shape-only certification command, real-if-key-present command, docs-refresh report, and release provider gate.

- [ ] **Step 4: Run the targeted test and confirm pass**

Run:

```powershell
python -m pytest tests/test_provider_certification.py::test_release_check_fails_when_requested_provider_has_no_shape_certification -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Run integration verification**

Run:

```powershell
python -m pytest tests/test_provider_certification.py -q
pf-agent provider certify --all --shape-only --write-report
```

Expected: command exits 0 and writes only the artifacts named in this card.

- [ ] **Step 6: Record commit boundary**

```powershell
git add src/proseforge_agent/llm/certification.py tests
git commit -m "feat: add provider certification workflow"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Verification

```powershell
python -m pytest tests/test_provider_certification.py -q
pf-agent provider certify --all --shape-only --write-report
```

## Acceptance

- Every requested provider needs at least shape certification for release.
- Real smoke is optional and skipped cleanly when keys are absent.
- Records include checked date and official source URLs.

## Commit Boundary

Commit after this card passes verification. Do not start the next card with failing tests or unreviewed artifacts from this card.
