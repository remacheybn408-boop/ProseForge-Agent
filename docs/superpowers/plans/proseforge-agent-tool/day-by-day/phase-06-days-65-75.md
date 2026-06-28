# Phase 06: CLI, Reports, Extensions, And Operator UX

Dates: 2026-08-29 to 2026-09-08.

Goal: make the product maintainable, extensible, and comfortable for a writer or engineer to operate.

## Day 65: 2026-08-29, CLI Command Audit

Primary objective: make the command surface coherent.

Context to read:

- `tasks/15-cli-and-reports.md`
- All implemented CLI commands.

Work blocks:

- Morning: list every CLI command and group by project, provider, memory, retrieve, plan, daily, chapter, workflow, report, and extension.
- Midday: normalize option names, output modes, dry-run flags, write flags, and config flags.
- Afternoon: add CLI help tests for every command group.
- Closeout: generate command reference.

Expected outputs:

- Command reference.
- CLI consistency tests.
- Updated help text.

Verification:

```powershell
python -m pytest -q tests
pf-agent --help
pf-agent report command-reference --write
```

Acceptance checklist:

- Command names are predictable.
- Destructive operations require explicit write or force mode.
- Dry-run is available where filesystem changes are possible.
- Help text shows examples for major workflows.

Stop condition:

- Stop when the CLI feels like one product.

## Day 66: 2026-08-30, Report Renderer Hardening

Primary objective: standardize all reports.

Context to read:

- `tasks/15-cli-and-reports.md`
- Planning, memory, provider, and workflow reports.

Work blocks:

- Morning: define report header contract: project, date, command, config, provider route, source files, status, and artifact links.
- Midday: implement shared report renderer for Markdown, JSON, and terminal summary.
- Afternoon: add snapshot tests for provider certification, memory audit, daily workbook, chapter review, and phase closeout.
- Closeout: generate full demo report pack.

Expected outputs:

- Shared report renderer.
- Snapshot tests.
- Demo report pack.

Verification:

```powershell
python -m pytest -q tests
pf-agent report all --project demo --write
```

Acceptance checklist:

- All reports share recognizable structure.
- JSON reports are stable for automation.
- Markdown reports are readable by a non-engineer.
- Reports include acceptance status and next action.

Stop condition:

- Stop when reports can serve as project management artifacts.

## Day 67: 2026-08-31, Extension API

Primary objective: create a stable foundation for future expansion.

Context to read:

- `tasks/16-extension-foundation-and-docs.md`
- `architecture/07-extension-foundation.md`

Work blocks:

- Morning: define extension points: provider, memory backend, retriever, workflow step, report renderer, gate, prompt pack, market analyzer, and export target.
- Midday: implement extension registry and discovery mechanism.
- Afternoon: add tests for registering, listing, version checking, disabled extension, and extension error isolation.
- Closeout: create one sample extension.

Expected outputs:

- Extension registry.
- Sample extension.
- Extension tests.

Verification:

```powershell
python -m pytest -q tests
pf-agent extension list
```

Acceptance checklist:

- Extensions cannot mutate core state without explicit hooks.
- Version compatibility is checked.
- Failed extensions do not crash unrelated commands.
- Sample extension demonstrates the pattern.

Stop condition:

- Stop when future features have a sanctioned place to attach.

## Day 68: 2026-09-01, Prompt Pack System

Primary objective: make prompts maintainable and swappable.

Context to read:

- Extension API.
- Draft, review, rewrite, memory, and planning prompt contracts.

Work blocks:

- Morning: define prompt pack structure with metadata, role, language, genre, version, input schema, output schema, and tests.
- Midday: implement prompt pack loader and validator.
- Afternoon: add tests for missing variable, invalid output schema, wrong role, and pack override.
- Closeout: create default professional-novel prompt pack.

Expected outputs:

- Prompt pack loader.
- Default prompt pack.
- Prompt tests.

Verification:

```powershell
python -m pytest -q tests
pf-agent prompt list
pf-agent prompt validate --pack default-professional-novel
```

Acceptance checklist:

- Prompts are not buried inside workflow code.
- Prompt packs can target genre or language without changing engine logic.
- Output schemas are validated.
- The default pack covers planning, drafting, review, rewrite, and memory.

Stop condition:

- Stop when prompt iteration is safe and versioned.

## Day 69: 2026-09-02, Data Privacy And Local Mode

Primary objective: give operators control over what leaves the machine.

Context to read:

- Provider routing policy.
- Memory schema privacy class.

Work blocks:

- Morning: define privacy classes for memory and artifacts: public, project_internal, sensitive, local_only, and never_send.
- Midday: implement privacy filter before provider calls.
- Afternoon: add tests for blocked provider call, redacted evidence pack, local-only route, and audit logging.
- Closeout: generate privacy report for demo project.

Expected outputs:

- Privacy filter.
- Privacy tests.
- Privacy report.

Verification:

```powershell
python -m pytest -q tests
pf-agent privacy audit --project demo --write-report
```

Acceptance checklist:

- Sensitive memory is never sent to a remote provider without policy allowance.
- Redactions are visible in logs.
- Router can enforce domestic-only, foreign-only, and local-only policies.
- Privacy violations fail before network calls.

Stop condition:

- Stop when model routing respects project confidentiality.

## Day 70: 2026-09-03, Cost And Usage Accounting

Primary objective: track provider usage for professional production budgeting.

Context to read:

- Provider response usage fields.
- Daily and weekly workbook reports.

Work blocks:

- Morning: define usage record: provider, model, role, tokens or billed units, estimated cost, latency, cache status, workflow step, and artifact id.
- Midday: implement usage ledger and report command.
- Afternoon: add tests for fake provider usage, missing price config, monthly totals, and per-role totals.
- Closeout: generate demo usage report.

Expected outputs:

- Usage ledger.
- Cost report.
- Tests.

Verification:

```powershell
python -m pytest -q tests
pf-agent usage report --project demo --month 2026-09 --write
```

Acceptance checklist:

- Usage is attributed to workflow steps.
- Missing price information is labeled clearly.
- Reports show cost by provider, role, and date.
- Daily recommendations can consider budget limits.

Stop condition:

- Stop when provider choice can include budget evidence.

## Day 71: 2026-09-04, Observability And Debug Logs

Primary objective: make agent behavior diagnosable.

Context to read:

- Workflow state.
- Provider certification and retrieval logs.

Work blocks:

- Morning: define event types: command_started, provider_call, retrieval_run, memory_write, workflow_transition, report_written, error, and warning.
- Midday: implement structured logging with redaction.
- Afternoon: add tests for event emission, secret redaction, log rotation, and trace id propagation.
- Closeout: run a workflow and inspect trace.

Expected outputs:

- Structured logger.
- Trace id propagation.
- Logging tests.

Verification:

```powershell
python -m pytest -q tests
pf-agent workflow trace --project demo --last
```

Acceptance checklist:

- Every major workflow has a trace id.
- Secrets are not written to logs.
- Logs help explain provider and retrieval decisions.
- Error reports point to relevant artifacts.

Stop condition:

- Stop when debugging does not require guessing.

## Day 72: 2026-09-05, Documentation For Operators

Primary objective: write practical docs for writers and operators.

Context to read:

- Command reference.
- Daily workflow docs.

Work blocks:

- Morning: write quickstart: init, config, provider certify, intake, phase plan, daily workbook, chapter run, memory review, export.
- Midday: write troubleshooting guide for provider keys, stale memory, failed review, export conflict, and privacy block.
- Afternoon: write provider setup guide for all requested providers.
- Closeout: run docs command examples in a demo environment.

Expected outputs:

- Quickstart guide.
- Troubleshooting guide.
- Provider setup guide.

Verification:

```powershell
python -m pytest -q tests
pf-agent docs check-examples
```

Acceptance checklist:

- A new user can run the fake-provider demo from docs.
- Provider setup names required environment variables.
- Troubleshooting entries include commands to run.
- Docs avoid promising real-provider support without certification.

Stop condition:

- Stop when the product can be adopted without oral explanation.

## Day 73: 2026-09-06, Developer Documentation

Primary objective: document how future developers extend the system.

Context to read:

- Extension API.
- Provider contract.
- Memory contract.

Work blocks:

- Morning: write provider-adapter development guide.
- Midday: write memory backend and retriever development guide.
- Afternoon: write workflow-step and report-renderer extension guide.
- Closeout: validate sample extension against docs.

Expected outputs:

- Developer guides.
- Sample extension validation.
- Architecture decision records.

Verification:

```powershell
python -m pytest -q tests
pf-agent extension validate samples/extensions/*
```

Acceptance checklist:

- Developers know which contracts are stable.
- Extension examples are runnable.
- Guides include tests and acceptance criteria.
- Future provider additions do not require core rewrites.

Stop condition:

- Stop when the foundation is truly extensible.

## Day 74: 2026-09-07, Packaging And Distribution Prep

Primary objective: prepare the tool for local installation and repeatable demos.

Context to read:

- Package skeleton.
- Docs quickstart.

Work blocks:

- Morning: define packaging metadata, console scripts, dependency groups, and optional extras for providers, vector stores, and reports.
- Midday: implement packaging checks and install test in a temporary environment.
- Afternoon: add tests for package import and CLI command after install.
- Closeout: create demo setup script or documented command sequence.

Expected outputs:

- Packaging metadata.
- Install verification.
- Demo setup workflow.

Verification:

```powershell
python -m pytest -q tests
python -m pip install -e .
pf-agent --help
```

Acceptance checklist:

- The package installs locally.
- Optional dependencies are documented.
- CLI entry point works after install.
- Demo setup does not require real provider keys.

Stop condition:

- Stop when installation no longer depends on the development shell.

## Day 75: 2026-09-08, Phase 06 Integration Gate

Primary objective: prove the product is operable and extensible.

Context to read:

- All Phase 06 files.
- Operator and developer docs.

Work blocks:

- Morning: run full tests, CLI help audit, docs examples, extension validation, usage report, and privacy audit.
- Midday: inspect reports for readability and consistency.
- Afternoon: fix operator-experience gaps.
- Closeout: write Phase 06 closeout report and Phase 07 start context.

Expected outputs:

- Passing operator UX tests.
- Docs example report.
- Phase 06 closeout report.

Verification:

```powershell
python -m pytest -q
pf-agent docs check-examples
pf-agent extension list
pf-agent privacy audit --project demo --write-report
```

Acceptance checklist:

- CLI, docs, reports, privacy, usage, and extensions work together.
- Writers can follow the quickstart.
- Developers can add providers or workflow steps.
- The release phase can focus on hardening, not missing foundations.

Stop condition:

- Stop when the tool is maintainable by someone other than its first author.
