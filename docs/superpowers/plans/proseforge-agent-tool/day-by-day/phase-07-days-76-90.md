# Phase 07: End-To-End Hardening And Release

Dates: 2026-09-09 to 2026-09-23.

Goal: verify the whole agent as a professional novel-production system.

## Day 76: 2026-09-09, End-To-End Fake Provider Demo

Primary objective: run the full product offline with the fake provider.

Context to read:

- `tasks/17-e2e-demo-and-release.md`
- Operator quickstart.

Work blocks:

- Morning: create a clean demo project from scratch.
- Midday: run init, provider certify, intake, market plan, volume plan, chapter roadmap, daily workbook, chapter run, memory review, export dry-run, closeout, and report pack.
- Afternoon: record every command and artifact path.
- Closeout: fix any docs or CLI mismatch found during the demo.

Expected outputs:

- Full fake-provider demo transcript.
- Demo artifact directory.
- Updated quickstart if needed.

Verification:

```powershell
python -m pytest -q
pf-agent demo run --provider fake --write-report
```

Acceptance checklist:

- Demo completes without real API keys.
- Every major subsystem produces an artifact.
- Generated daily workbook recommends the next day.
- Reports explain the completed workflow.

Stop condition:

- Stop when offline demo proves the product spine.

## Day 77: 2026-09-10, Real Provider Smoke Selection

Primary objective: decide which real providers to smoke-test in the local environment.

Context to read:

- Provider certification summary.
- Local environment variables.

Work blocks:

- Morning: run provider key detection without printing secrets.
- Midday: choose at least one available provider for real smoke test, preferring a low-cost or already-configured provider.
- Afternoon: run minimal real smoke for text generation and streaming if available.
- Closeout: record results and mark unavailable providers as not locally certified.

Expected outputs:

- Real-provider smoke report.
- Updated certification records.

Verification:

```powershell
pf-agent provider certify --all --real-if-key-present --write-report
```

Acceptance checklist:

- No secret values are printed.
- Providers without keys are skipped, not failed.
- Real smoke output is small and controlled.
- Certification status distinguishes shape-certified from real-certified.

Stop condition:

- Stop when at least one real-provider path is exercised or clearly impossible due to missing keys.

## Day 78: 2026-09-11, Real Provider Workflow Smoke

Primary objective: run a tiny workflow through a real provider when a key is available.

Context to read:

- Day 77 smoke report.
- Privacy policy.

Work blocks:

- Morning: select a small non-sensitive demo prompt.
- Midday: run chapter prepare and draft with the selected real provider, using strict token and cost limits.
- Afternoon: compare artifact structure with fake-provider output.
- Closeout: record cost, latency, and provider behavior.

Expected outputs:

- Real-provider workflow smoke report.
- Usage ledger entry.
- Provider behavior notes.

Verification:

```powershell
pf-agent chapter run --project demo --chapter 1 --until draft --provider-role drafter --real-provider-smoke
```

Acceptance checklist:

- Real provider call respects privacy and budget policy.
- Workflow artifacts remain contract-compatible.
- Usage is recorded.
- Failures route through normal recovery.

Stop condition:

- Stop when real-provider workflow compatibility is proven or key absence is documented.

## Day 79: 2026-09-12, Provider Fallback Drill

Primary objective: prove provider fallback works under failure.

Context to read:

- Fallback router.
- Workflow failure drills.

Work blocks:

- Morning: simulate primary provider failure for planner, drafter, critic, reviser, memory, and embedding roles.
- Midday: run fallback tests across domestic-only, foreign-only, privacy-strict, low-cost, and high-quality policies.
- Afternoon: inspect route explanations and workflow state.
- Closeout: update fallback docs.

Expected outputs:

- Fallback drill report.
- Router tests.
- Documentation updates.

Verification:

```powershell
python -m pytest -q tests
pf-agent provider drill-fallback --project demo --all-policies --write-report
```

Acceptance checklist:

- Fallback never violates privacy policy.
- Non-retryable errors do not loop forever.
- Route reports explain each skip and selection.
- Workflow state records both failed and successful provider attempts.

Stop condition:

- Stop when provider outage does not threaten project continuity.

## Day 80: 2026-09-13, Memory Stress Test

Primary objective: test memory with long-project volume.

Context to read:

- Memory audit and compaction docs.
- Retrieval performance expectations.

Work blocks:

- Morning: generate or import a large fixture with many chapters, characters, places, timeline events, and contradictions.
- Midday: run ingest, classify fixture outputs, index, retrieve, compact, and audit.
- Afternoon: measure retrieval latency, evidence pack size, duplicate rate, and contradiction detection.
- Closeout: tune indexing, compaction, or ranking thresholds.

Expected outputs:

- Memory stress report.
- Performance notes.
- Tuning changes if needed.

Verification:

```powershell
python -m pytest -q tests
pf-agent memory stress --project demo --write-report
```

Acceptance checklist:

- Retrieval remains usable at long-project scale.
- Evidence packs stay within configured token budgets.
- Audit detects seeded contradictions.
- Compaction does not lose sources.

Stop condition:

- Stop when memory scale risk is understood and controlled.

## Day 81: 2026-09-14, Chapter Quality Regression Suite

Primary objective: test writing workflow against representative novel scenarios.

Context to read:

- Chapter workflow tests.
- Editorial gate definitions.

Work blocks:

- Morning: create fixtures for action scene, emotional confession, reveal chapter, transition chapter, setup chapter, and climax chapter.
- Midday: run prepare, draft, review, rewrite, and accept dry path for each fixture using fake provider outputs.
- Afternoon: add regression tests for gate handling and memory update categories.
- Closeout: write quality-regression report.

Expected outputs:

- Chapter scenario fixtures.
- Regression tests.
- Quality report.

Verification:

```powershell
python -m pytest -q tests
pf-agent chapter regression --project demo --write-report
```

Acceptance checklist:

- Different chapter types exercise different gates.
- Fake fixtures catch workflow regressions.
- Review and rewrite loops are covered.
- Memory updates are scenario-specific.

Stop condition:

- Stop when chapter workflow is tested beyond one happy path.

## Day 82: 2026-09-15, Security And Secret Handling Review

Primary objective: verify keys and sensitive project content are protected.

Context to read:

- Privacy filter.
- Structured logging.
- Config handling.

Work blocks:

- Morning: audit environment variable handling, config loading, logs, reports, error messages, and provider request traces.
- Midday: add tests for key redaction, sensitive memory redaction, and no-secret report output.
- Afternoon: run a simulated failure with secret-like strings.
- Closeout: update security notes.

Expected outputs:

- Security audit report.
- Redaction tests.
- Security notes.

Verification:

```powershell
python -m pytest -q tests
pf-agent security audit --project demo --write-report
```

Acceptance checklist:

- API keys never appear in logs or reports.
- Sensitive memory obeys privacy policy.
- Provider errors are redacted before display.
- Security audit has no high-severity unresolved items.

Stop condition:

- Stop when secret leakage risk is actively tested.

## Day 83: 2026-09-16, Windows Path And Encoding Review

Primary objective: make sure the tool works in the user's Windows workspace.

Context to read:

- Config and workspace resolver.
- Report renderer.

Work blocks:

- Morning: test Windows paths with spaces, Chinese filenames, long paths, drive-letter paths, and mixed slashes.
- Midday: test UTF-8 reading and writing for Chinese manuscript text.
- Afternoon: add tests for path normalization and report links.
- Closeout: run demo commands from `$PROSEFORGE_AGENT_ROOT`.

Expected outputs:

- Windows path tests.
- Encoding tests.
- Compatibility report.

Verification:

```powershell
python -m pytest -q tests
pf-agent doctor --config configs/agent.example.yaml
```

Acceptance checklist:

- Paths with spaces work.
- Chinese manuscript text round-trips without corruption.
- Reports open from the Windows workspace.
- CLI examples match PowerShell syntax.

Stop condition:

- Stop when the user's operating environment is a first-class target.

## Day 84: 2026-09-17, Performance Budget Review

Primary objective: set and test performance budgets.

Context to read:

- Usage ledger.
- Memory stress report.
- Workflow traces.

Work blocks:

- Morning: define budgets for CLI startup, config load, provider route selection, memory search, evidence pack building, daily workbook generation, and report rendering.
- Midday: implement lightweight benchmark command.
- Afternoon: add tests that catch severe regressions without being flaky.
- Closeout: run benchmark on demo project.

Expected outputs:

- Performance budget file.
- Benchmark command.
- Performance report.

Verification:

```powershell
python -m pytest -q tests
pf-agent benchmark --project demo --write-report
```

Acceptance checklist:

- Common offline commands feel responsive.
- Memory retrieval latency is measured.
- Benchmarks produce useful trend data.
- Performance warnings do not block functional tests unless severe.

Stop condition:

- Stop when performance has numbers, not impressions.

## Day 85: 2026-09-18, Documentation Freeze Candidate

Primary objective: align docs with actual behavior.

Context to read:

- Operator docs.
- Developer docs.
- Demo transcript.

Work blocks:

- Morning: run every documented command example.
- Midday: update docs where command names, flags, paths, or outputs changed.
- Afternoon: verify provider setup guide includes all requested provider families.
- Closeout: mark docs as freeze candidate for release review.

Expected outputs:

- Updated docs.
- Docs example test output.
- Docs freeze report.

Verification:

```powershell
python -m pytest -q tests
pf-agent docs check-examples --strict
```

Acceptance checklist:

- Docs examples run.
- Provider setup covers OpenAI, Claude, Gemini, Grok, DeepSeek, Qwen, GLM, MiMo, MiniMax, and Doubao.
- Quickstart uses fake provider first.
- Real-provider steps are clearly optional.

Stop condition:

- Stop when documentation no longer lies by accident.

## Day 86: 2026-09-19, Release Candidate Build

Primary objective: prepare a release candidate.

Context to read:

- Packaging prep.
- Test matrix.

Work blocks:

- Morning: run full test suite and packaging check.
- Midday: build release artifact or local install package.
- Afternoon: install from the built artifact in a clean environment and run quickstart demo.
- Closeout: write release candidate notes.

Expected outputs:

- Release candidate artifact.
- Install test report.
- Release notes draft.

Verification:

```powershell
python -m pytest -q
python -m build
python -m pip install dist/*.whl
pf-agent demo run --provider fake --write-report
```

Acceptance checklist:

- Tests pass before build.
- Built artifact installs.
- CLI works after install.
- Fake-provider demo works from installed package.

Stop condition:

- Stop when the release can be tested outside the source tree.

## Day 87: 2026-09-20, User Acceptance Walkthrough

Primary objective: test the tool as a novelist would use it.

Context to read:

- Quickstart.
- Daily workbook examples.

Work blocks:

- Morning: start from a blank project and follow writer-facing docs without reading developer docs.
- Midday: create project intake, generate phase plan, generate daily workbook, draft one chapter, review, rewrite, accept, and close out.
- Afternoon: note every confusing command, report, or missing explanation.
- Closeout: fix high-impact usability issues.

Expected outputs:

- User acceptance notes.
- Usability fixes.
- Updated quickstart if needed.

Verification:

```powershell
pf-agent demo run --provider fake --mode writer-walkthrough --write-report
```

Acceptance checklist:

- A writer can understand the next action at each step.
- Reports avoid engineering-only language where possible.
- Daily workbook is useful as the day's working document.
- Memory review is understandable and not frightening.

Stop condition:

- Stop when the product feels usable for writing work.

## Day 88: 2026-09-21, Final Risk Burn-Down

Primary objective: close or document remaining release risks.

Context to read:

- `appendices/03-risk-register.md`
- Phase closeout reports.

Work blocks:

- Morning: review every risk and classify as closed, mitigated, accepted, or blocking.
- Midday: fix blocking risks that can be handled in one day.
- Afternoon: document accepted risks with impact, workaround, and owner.
- Closeout: update release notes with known limitations.

Expected outputs:

- Updated risk register.
- Known limitations section.
- Final mitigation report.

Verification:

```powershell
python -m pytest -q
pf-agent risk report --write
```

Acceptance checklist:

- No blocking release risks remain.
- Accepted risks have workarounds.
- Provider uncertainty is handled through certification status.
- Memory and privacy risks have explicit mitigations.

Stop condition:

- Stop when release risk is visible and acceptable.

## Day 89: 2026-09-22, Final Regression And Artifact Review

Primary objective: run final verification and inspect deliverables.

Context to read:

- Test matrix.
- Release candidate notes.

Work blocks:

- Morning: run full tests, docs strict check, fake demo, provider shape certification, memory stress, security audit, and Windows compatibility check.
- Midday: inspect generated reports for broken links, missing dates, missing acceptance states, and secret leakage.
- Afternoon: fix final regressions or mark release as blocked if a critical issue remains.
- Closeout: write final verification report.

Expected outputs:

- Final verification report.
- Clean report pack.
- Updated release notes.

Verification:

```powershell
python -m pytest -q
pf-agent docs check-examples --strict
pf-agent provider certify --all --shape-only --write-report
pf-agent demo run --provider fake --write-report
pf-agent security audit --project demo --write-report
```

Acceptance checklist:

- All critical verification commands pass.
- Reports include dates and acceptance states.
- No secrets are visible.
- Release notes match actual status.

Stop condition:

- Stop when the release candidate is ready for final sign-off.

## Day 90: 2026-09-23, Release Sign-Off

Primary objective: sign off ProseForge Agent as a professional novel-writing workflow tool.

Context to read:

- Final verification report.
- Release notes.
- Risk register.

Work blocks:

- Morning: review the final product against the original requirements.
- Midday: confirm ProseForge functions, stage plans, daily workbooks, extensible foundation, deep memory, automatic retrieval, and broad model adaptation.
- Afternoon: tag or record the release state, archive demo artifacts, and write next-roadmap recommendations.
- Closeout: deliver final release sign-off summary.

Expected outputs:

- Release sign-off document.
- Archived demo artifacts.
- Next-roadmap proposal.

Verification:

```powershell
python -m pytest -q
pf-agent demo run --provider fake --write-report
pf-agent release check --project demo --write-report
```

Acceptance checklist:

- ProseForge Agent can run a complete professional writing workflow.
- Daily work recommendations are date-based and state-based.
- Deep memory and retrieval are functional and auditable.
- Provider adaptation covers all requested model families with certification status.
- Extension points are documented and tested.
- Known limitations are explicit.

Stop condition:

- Stop when the original request is satisfied in a release-ready form.
