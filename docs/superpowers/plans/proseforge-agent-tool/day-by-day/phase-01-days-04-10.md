# Phase 01: Foundation And Adapter Spine

Dates: 2026-06-29 to 2026-07-05.

Goal: create the smallest runnable ProseForge Agent foundation with config, workspace, ProseForge bridge, provider contract, and fake model.

## Day 04: 2026-06-29, Package Skeleton

Primary objective: create the Python package, CLI entry point, tests folder, and lintable structure.

Context to read:

- `tasks/01-package-skeleton.md`
- `architecture/02-system-architecture.md`

Work blocks:

- Morning: create package directories for `agent`, `cli`, `config`, `providers`, `memory`, `retrieval`, `workflow`, `reports`, and `extensions`.
- Midday: add CLI command group with `pf-agent --help`, `pf-agent version`, and `pf-agent doctor`.
- Afternoon: add first unit tests for CLI import, version output, and package metadata.
- Closeout: run tests and record command output in daily notes.

Expected outputs:

- Package skeleton under the selected source directory.
- Test skeleton under `tests`.
- Project metadata file.

Verification:

```powershell
python -m pytest -q
pf-agent --help
```

Acceptance checklist:

- The CLI imports without touching provider keys, network, or project files.
- `pf-agent doctor` runs and reports missing optional dependencies clearly.
- Test command succeeds on a clean local environment.
- Folder names match the architecture plan.

Stop condition:

- Stop when a new contributor can run the package help command.

## Day 05: 2026-06-30, Config And Workspace Contract

Primary objective: define how projects, providers, memory stores, and output paths are configured.

Context to read:

- `tasks/02-config-and-workspace.md`
- `appendices/01-data-contracts.md`

Work blocks:

- Morning: design `agent.example.yaml` with project root, ProseForge root, provider profiles, memory backend, retrieval backend, report paths, and privacy settings.
- Midday: implement config parser with validation errors that name the bad field and expected type.
- Afternoon: implement workspace resolver for project slug, manuscript path, memory path, reports path, and daily workbook path.
- Closeout: test config load, invalid config, missing directory, and path normalization on Windows.

Expected outputs:

- Config schema.
- Example config.
- Workspace resolver.
- Config tests.

Verification:

```powershell
python -m pytest -q tests
pf-agent doctor --config configs/agent.example.yaml
```

Acceptance checklist:

- The example config is valid.
- Missing API keys do not break offline commands.
- Paths resolve correctly from `$PROSEFORGE_AGENT_ROOT`.
- Error messages are useful enough for a non-engineer operator.

Stop condition:

- Stop when config and workspace can be trusted by all later tasks.

## Day 06: 2026-07-01, ProseForge Engine Discovery

Primary objective: detect and inspect the existing ProseForge engine without rewriting it.

Context to read:

- `tasks/03-proseforge-engine-adapter.md`
- `architecture/03-proseforge-engine-integration.md`
- Existing `$PROSEFORGE_ROOT` structure.

Work blocks:

- Morning: locate ProseForge project slots, pipeline commands, guards, reports, exports, and memory-related files.
- Midday: implement `ProseForgeAdapter.discover()` that returns version, capabilities, paths, and missing features.
- Afternoon: add tests using fixture directories that mimic the ProseForge layout.
- Closeout: run adapter discovery against the real local ProseForge folder in read-only mode.

Expected outputs:

- Discovery adapter.
- ProseForge capability object.
- Fixture tests.

Verification:

```powershell
python -m pytest -q tests
pf-agent proseforge inspect --root $PROSEFORGE_ROOT
```

Acceptance checklist:

- The adapter reads existing ProseForge layout without modifying it.
- Missing capabilities are reported as warnings with recovery advice.
- Discovery result can be serialized to JSON.
- Tests cover present, missing, and malformed ProseForge roots.

Stop condition:

- Stop when the agent can describe what ProseForge can do on this machine.

## Day 07: 2026-07-02, ProseForge Action Bridge

Primary objective: wrap ProseForge actions as safe, typed operations.

Context to read:

- `tasks/03-proseforge-engine-adapter.md`
- ProseForge command and pipeline docs discovered on Day 06.

Work blocks:

- Morning: define action objects for project status, slot creation, pipeline run, guard run, report generation, and export.
- Midday: implement dry-run mode so future workflows can preview actions.
- Afternoon: add action result contracts with stdout, stderr, artifacts, warnings, duration, and status.
- Closeout: test dry-run behavior and one real read-only action if available.

Expected outputs:

- Typed action bridge.
- Dry-run implementation.
- Action-result tests.

Verification:

```powershell
python -m pytest -q tests
pf-agent proseforge status --root $PROSEFORGE_ROOT --dry-run
```

Acceptance checklist:

- Every bridge call has a typed input and typed output.
- Dry-run never writes project artifacts.
- Failures preserve enough detail for workflow recovery.
- The bridge never shells out with unescaped user text.

Stop condition:

- Stop when later workflows can call ProseForge through one stable interface.

## Day 08: 2026-07-03, Provider Contract And Fake Model

Primary objective: implement the provider abstraction and deterministic fake provider.

Context to read:

- `tasks/04-provider-contracts-and-fake.md`
- `providers/01-normalized-provider-contract.md`

Work blocks:

- Morning: define provider request, provider response, stream event, tool call, usage, finish reason, and provider error types.
- Midday: implement `FakeProvider` with deterministic text, stream chunks, tool-call echo, refusal simulation, timeout simulation, and rate-limit simulation.
- Afternoon: add tests for sync generation, streaming, retries, cancellation, and error mapping.
- Closeout: make one CLI command call the fake provider.

Expected outputs:

- Provider interface.
- Fake provider.
- Provider test suite.

Verification:

```powershell
python -m pytest -q tests
pf-agent provider smoke --provider fake
```

Acceptance checklist:

- All workflows can be tested without paid APIs.
- Fake provider can simulate success and common failures.
- Usage accounting exists even for fake responses.
- Provider errors use normalized categories.

Stop condition:

- Stop when provider-dependent work can proceed offline.

## Day 09: 2026-07-04, OpenAI-Compatible Transport Spine

Primary objective: build the shared transport for providers that expose OpenAI-compatible endpoints.

Context to read:

- `tasks/05-openai-compatible-provider.md`
- `providers/02-domestic-provider-matrix.md`
- `providers/03-foreign-provider-matrix.md`

Work blocks:

- Morning: implement request builder for chat completions style endpoints with configurable base URL, headers, model, timeout, stream flag, and tool schema handling.
- Midday: implement response parser for content, tool calls, usage, finish reason, refusal-like signals, and provider-specific raw metadata.
- Afternoon: implement fake HTTP transport tests for success, stream, 401, 429, 500, malformed JSON, and partial stream.
- Closeout: connect provider smoke command to this transport in shape-test mode.

Expected outputs:

- OpenAI-compatible transport.
- Fake HTTP tests.
- Provider smoke command with `--shape-only`.

Verification:

```powershell
python -m pytest -q tests
pf-agent provider smoke --provider openai-compatible --shape-only
```

Acceptance checklist:

- Base URL and model are pure config values.
- No provider key is logged.
- Shape tests pass without network.
- Error mapping is independent of vendor names.

Stop condition:

- Stop when domestic compatible providers can share this transport.

## Day 10: 2026-07-05, Phase 01 Integration Gate

Primary objective: prove the foundation works together before adding many providers.

Context to read:

- Phase 01 files.
- `phases/01-phase-acceptance-gates.md`

Work blocks:

- Morning: run package, config, workspace, ProseForge discovery, fake provider, and compatible transport tests together.
- Midday: fix integration mismatches and update data contracts if code uncovered a better field name.
- Afternoon: write a Phase 01 closeout report with commands, artifacts, open risks, and Day 11 start context.
- Closeout: tag the phase status in project notes.

Expected outputs:

- Phase 01 closeout report.
- Passing foundation test suite.
- Known-risk list for provider phase.

Verification:

```powershell
python -m pytest -q
pf-agent doctor --config configs/agent.example.yaml
pf-agent provider smoke --provider fake
```

Acceptance checklist:

- The package has a stable folder spine.
- The agent can inspect ProseForge.
- The agent can call a fake model.
- The agent can shape-test OpenAI-compatible requests.
- The next phase can add providers without changing the provider contract.

Stop condition:

- Stop when the foundation is stable enough for provider expansion.
