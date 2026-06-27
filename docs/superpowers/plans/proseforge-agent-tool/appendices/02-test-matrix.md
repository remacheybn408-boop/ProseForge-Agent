# Test Matrix

## Unit Tests

| Area | Test File | Required Behaviors |
| --- | --- | --- |
| Package | `tests/test_package.py` | import package, version, base error |
| Config | `tests/test_config.py` | load YAML, resolve paths, required fields |
| Workspace | `tests/test_workspace.py` | create directory layout |
| Engine adapter | `tests/test_proseforge_adapter.py` | command building, validation, run result |
| Provider registry | `tests/test_provider_registry.py` | role routing, default fallback |
| Fake provider | `tests/test_llm_fake_and_routing.py` | deterministic output |
| OpenAI-compatible provider | `tests/test_llm_openai_compatible.py` | request shape, response parse, missing key |
| Native providers | `tests/test_llm_native_adapters.py` | Anthropic/Gemini request and parse |
| Memory store | `tests/test_memory_store.py` | schema, add, search, link, retrieval logs |
| Memory classifier | `tests/test_memory_classifier.py` | type classification |
| Memory compactor | `tests/test_memory_compactor.py` | duplicate merge |
| Retrieval router | `tests/test_retrieval_router.py` | query construction |
| Evidence pack | `tests/test_evidence_pack.py` | must_keep, degraded, conflicts |
| Phase plan | `tests/test_phase_plan.py` | required phases, markdown |
| Daily workbook | `tests/test_daily_workbook.py` | date, focus, closeout |
| Recommendation | `tests/test_daily_recommendation.py` | state to next action |
| Workflow state | `tests/test_workflow_state.py` | save, load, append step |
| Recovery | `tests/test_workflow_recovery.py` | retry planning |
| Chapter workflow | `tests/test_chapter_workflow.py` | ordered steps |
| Draft writer | `tests/test_draft_writer.py` | versioned draft path |
| Prompt pack | `tests/test_prompt_pack.py` | evidence injection |
| Rewrite workflow | `tests/test_rewrite_accept_workflow.py` | rewrite, save, accept |
| CLI | `tests/test_cli.py` | commands, output, exit codes |
| Reports | `tests/test_reports.py` | markdown and JSON write |
| Extensions | `tests/test_extension_registry.py` | register, get, list |
| E2E fake | `tests/test_end_to_end_fake.py` | fake full run |

## Integration Tests

Safe integration checks:

```powershell
python $PROSEFORGE_ROOT\plugin\proseforge-codex\scripts\nf_project.py --action status --project-root $PROSEFORGE_ROOT
```

Adapter integration with real root:

```powershell
pf-agent status --config configs/agent.example.yaml --json
```

## Full Verification

```powershell
python -m pytest -q
```

## Test Rules

- No network calls in unit tests.
- No real API keys in tests.
- Use fake provider for workflow tests.
- Use fake engine for mutating workflow tests.
- Real ProseForge smoke tests must be read-only unless a demo slot is explicitly created.
