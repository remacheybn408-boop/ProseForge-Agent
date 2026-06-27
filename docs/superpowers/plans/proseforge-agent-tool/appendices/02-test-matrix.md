# Test Matrix

## Goal

The test matrix verifies ProseForge Agent as a complete agent product: novel workflow, chat, memory, provider routing, installation, diagnostics, and native operation on Windows, macOS, and Linux.

## Unit Tests

| Area | Test File | Required Behaviors |
| --- | --- | --- |
| Package | `tests/test_package.py` | import package, version, base errors |
| Config | `tests/test_config.py` | environment expansion, portable paths, required fields |
| Workspace | `tests/test_workspace.py` | project-local and native workspace layouts |
| Engine adapter | `tests/test_proseforge_adapter.py` | discovery, dry-run commands, result serialization |
| Provider registry | `tests/test_provider_registry.py` | role routing, default fallback, missing key skips |
| Fake provider | `tests/test_llm_fake_and_routing.py` | deterministic output, stream, tool-call simulation |
| OpenAI-compatible transport | `tests/test_openai_compatible_provider.py` | request shape, response parse, stream parse, error mapping |
| Provider profiles | `tests/test_provider_*.py` | each requested provider has shape tests and certification |
| Capability probes | `tests/test_provider_probes.py` | text, stream, JSON, tool, safety, real-mode guard |
| Provider router | `tests/test_provider_router.py` | domestic, foreign, local, privacy, cost, fallback policies |
| Memory store | `tests/test_memory_store.py` | add, list, supersede, export, audit source |
| Memory ingestion | `tests/test_memory_ingestion.py` | candidates, source refs, dry-run |
| Memory compaction | `tests/test_memory_compaction.py` | source-preserving summaries and contradiction retention |
| Retrieval router | `tests/test_retrieval_router.py` | intent queries, ranking, explanations |
| Evidence pack | `tests/test_evidence_pack.py` | hard canon, warnings, token budget, citations |
| Phase plan | `tests/test_phase_plan_generator.py` | intake, arcs, gates, source refs |
| Daily workbook | `tests/test_daily_workbook.py` | date, objective, state-based next action |
| Workflow state | `tests/test_workflow_state.py` | transitions, audit, retry, resume |
| Chapter lifecycle | `tests/test_chapter_lifecycle.py` | prepare, draft, artifacts, state |
| Rewrite and accept | `tests/test_rewrite_accept.py` | review gates, force audit, accepted artifact |
| CLI | `tests/test_cli_commands.py` | command groups, help, output modes |
| Reports | `tests/test_reports.py` | Markdown, JSON, terminal summaries |
| Extensions | `tests/test_extensions.py` | registry, version compatibility, isolation |
| Agent kernel | `tests/test_agent_kernel.py` | turn loop, permission, events, memory candidates |
| Intent router | `tests/test_intent_router.py` | chat modes, intents, permissions, ambiguity |
| Tool policy | `tests/test_agent_tools_permissions.py` | read/write/system permission gates |
| Chat sessions | `tests/test_chat_session_store.py` | transcript persistence, UTF-8, export |
| Chat CLI | `tests/test_chat_cli_repl.py` | REPL, one-shot, slash commands, EOF |
| Chat prompt protocol | `tests/test_chat_prompt_protocol.py` | mode prompts, canon separation, permission ceiling |
| Chat retrieval | `tests/test_chat_retrieval_citations.py` | project answers with cited sources |
| Chat memory | `tests/test_chat_memory_preferences.py` | preferences and project decisions as candidates |
| Chat handoff | `tests/test_chat_workflow_handoff.py` | approval package for workflow starts |
| Event bus | `tests/test_agent_events_jobs.py` | event traces and background job reports |
| First-run wizard | `tests/test_first_run_onboarding.py` | config, workspace, provider stub, doctor report |
| Installation doctor | `tests/test_installation_doctor.py` | OS, Python, config, root, provider, encoding, recovery |
| App directories | `tests/test_app_dirs.py` | Windows, macOS, Linux, portable mode |
| Platform IO | `tests/test_platform_io.py` | shell quoting, UTF-8, paths with spaces |
| Native secrets | `tests/test_native_secret_storage.py` | Credential Manager, Keychain, Secret Service, env fallback |
| Provider setup wizard | `tests/test_provider_setup_wizard.py` | profile writes, secret storage, no secret leaks |
| Python install flows | `tests/test_python_install_flows.py` | source, pip, pipx, console entrypoint |
| Binary packaging | `tests/test_binary_packaging.py` | artifact manifest and smoke command |
| Windows native | `tests/test_windows_native_support.py` | PowerShell, Credential Manager, UTF-8, long paths |
| macOS native | `tests/test_macos_native_support.py` | Keychain, app dirs, zsh, package metadata |
| Linux native | `tests/test_linux_native_support.py` | XDG, Secret Service, shell support, local models |
| Shell integration | `tests/test_shell_completions_launchers.py` | PowerShell, Bash, Zsh, Fish |
| Migration | `tests/test_upgrade_migration_backup.py` | backup, schema migration, rollback notes |
| Uninstall | `tests/test_uninstall_data_retention.py` | preserve data by default, explicit deletion |
| Local models | `tests/test_offline_local_model_setup.py` | Ollama, LM Studio, vLLM, llama.cpp profiles |
| Local service API | `tests/test_local_agent_service_api.py` | health, chat, sessions, provider status |
| Profiles/personas | `tests/test_agent_profiles_personas.py` | writer, editor, operator, general profiles |
| Support bundle | `tests/test_support_bundle.py` | redaction, trace ids, doctor, provider status |
| Native QA matrix | `tests/test_native_qa_matrix.py` | required checks for each OS |
| Complete release gate | `tests/test_complete_agent_release_gate.py` | blocks missing chat, install, provider, memory, native QA |
| Usage metering | `tests/test_provider_usage_metering.py` | token/cost recording, budget block before call, bounded backoff |
| Safety guard | `tests/test_agent_safety_guard.py` | untrusted content cannot escalate; injection patterns flagged |
| Streaming | `tests/test_streaming_responses.py` | aggregated stream equals non-streaming; single-chunk fallback |
| CI pipeline | `tests/test_ci_pipeline.py` | three-OS matrix, pytest step, QA-matrix parity |
| Concurrency | `tests/test_concurrency_locking.py` | serialized writers, clean lock timeout, SQLite busy retry |

## Cross-Platform Native Matrix

| Capability | Windows | macOS | Linux |
| --- | --- | --- | --- |
| Source install | `python -m pip install -e .` | `python -m pip install -e .` | `python -m pip install -e .` |
| pipx install | required | required | required |
| Standalone binary smoke | required | required | required |
| `pf-agent init` | required | required | required |
| `pf-agent doctor` | required | required | required |
| `pf-agent chat --message` | required | required | required |
| UTF-8 Chinese text | required | required | required |
| Paths with spaces | required | required | required |
| Native config dir | required | required | required |
| Native secret backend | Credential Manager | Keychain | Secret Service or env fallback |
| Shell completion | PowerShell | Zsh and Bash | Bash, Zsh, Fish |
| Uninstall dry-run | required | required | required |

## Safe Integration Checks

Portable ProseForge adapter check:

```powershell
pf-agent proseforge inspect --root "${PROSEFORGE_ROOT}" --dry-run
```

Provider shape certification:

```powershell
pf-agent provider certify --all --shape-only --write-report
```

Chat smoke:

```powershell
pf-agent chat --message "hello" --provider fake --no-project
pf-agent chat --message "今天写什么？" --project demo --provider fake
```

Install smoke:

```powershell
pf-agent init --dry-run
pf-agent doctor --json
```

Complete release smoke:

```powershell
pf-agent demo run --provider fake --write-report
pf-agent release check --complete-agent --write-report
```

## Full Verification

```powershell
python -m pytest -q
```

## Test Rules

- No network calls in unit tests.
- No real API keys in tests.
- Use fake provider for workflow and chat tests.
- Use fake engine for mutating workflow tests.
- Real ProseForge smoke tests are read-only unless a demo slot is explicitly created.
- Real provider smoke tests run only with explicit real-mode flags.
- Native OS tests must simulate all three operating systems in unit tests and record manual evidence before release.
- No test fixture may contain machine-specific absolute paths.
- Secret-like strings must be redacted from logs, reports, support bundles, and assertion output.
