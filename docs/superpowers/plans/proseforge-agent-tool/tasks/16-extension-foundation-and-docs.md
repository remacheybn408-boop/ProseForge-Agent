# Task 16: Extension Foundation And Docs

## Goal

Create extension points and documentation so future providers, prompts, memory backends, and workflow steps do not require core rewrites.

## Architecture Notes

Extensions are opt-in, versioned, and isolated from unrelated commands.

Read before starting:

- ../architecture/02-system-architecture.md
- ../appendices/01-data-contracts.md
- 00-task-index.md

## Files

- Create `src/proseforge_agent/extensions/base.py`
- Create `src/proseforge_agent/extensions/registry.py`
- Create `samples/extensions/sample_gate.py`
- Create `docs/operator-quickstart.md`
- Create `docs/developer-extensions.md`
- Create `tests/test_extensions.py`

## Interfaces / Contracts

Extension points: provider, memory_backend, retriever, workflow_step, report_renderer, gate, prompt_pack, market_analyzer, export_target. Each extension declares id, version, compatible_agent_range, and capabilities.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_extensions.py::test_extension_registry_rejects_incompatible_version`**

```python
def test_extension_registry_rejects_incompatible_version():
    extension = SampleExtension(id="sample", compatible_agent_range=">=9.0")
    with pytest.raises(ExtensionError, match="compatible"):
        ExtensionRegistry(agent_version="0.1.0").register(extension)
```

- [ ] **Step 2: Run the targeted test and confirm failure**

Run:

```powershell
python -m pytest tests/test_extensions.py::test_extension_registry_rejects_incompatible_version -q
```

Expected: FAIL because extension registry is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement extension protocol, registry, compatibility check, disabled extension behavior, error isolation, sample gate extension, and operator/developer docs.

- [ ] **Step 4: Run the targeted test and confirm pass**

Run:

```powershell
python -m pytest tests/test_extensions.py::test_extension_registry_rejects_incompatible_version -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Run integration verification**

Run:

```powershell
python -m pytest tests/test_extensions.py -q
pf-agent extension list
```

Expected: command exits 0 and writes only the artifacts named in this card.

- [ ] **Step 6: Record commit boundary**

```powershell
git add src/proseforge_agent/extensions/base.py tests
git commit -m "feat: add extension foundation and docs"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Verification

```powershell
python -m pytest tests/test_extensions.py -q
pf-agent extension list
```

## Acceptance

- Failed extensions do not crash unrelated commands.
- Docs explain relationship between `$PROSEFORGE_ROOT` and the Agent workspace.
- Sample extension is validated by tests.

## Commit Boundary

Commit after this card passes verification. Do not start the next card with failing tests or unreviewed artifacts from this card.
