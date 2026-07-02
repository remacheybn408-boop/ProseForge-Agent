# Task 188: First-Run Bootstrap Auto-Trigger / 首次运行自动引导

## Goal

Auto-trigger the existing first-run bootstrap when `pf-agent` is invoked on a
machine that has no provider configuration, no workspace, or no consented
telemetry preferences. Today Task 80 (`setup.first_run.FirstRunBootstrap`) and
Task 46 (`install.first_run.FirstRunWizard`) both exist but must be launched
explicitly via `pf-agent setup` / `pf-agent init`. New users don't know that.

## Agent Product Requirement

Task 186 makes bare `pf-agent` enter chat. That entry needs a safety net: if
the user's machine has never been provisioned, we need a bounded
"welcome → pick provider → pick workspace → consent" flow that ends with a
working chat REPL, not a config error.

## Architecture Notes

We compose (not replace) the two existing wizards:

- **`install.first_run.FirstRunWizard`** — cross-platform onboarding
  (already used at `cli.py:5273`).
- **`setup.first_run.FirstRunBootstrap`** — deeper bootstrap that seeds
  configs (already used at `cli.py:3747`).

Add a new **auto-trigger detector** `install.auto_trigger.AutoBootstrap` that
answers a single question:

> "Given the current environment, should we auto-run onboarding?"

It reads (never writes) three signals:

- Config: does `load_agent_config()` resolve, and does the resolved provider
  have a usable secret in `native_secret_storage` or env?
- Workspace: does `WorkspaceLayout.ensure()` succeed, and is `.pf-agent/`
  populated at least at v1 layout?
- Consent marker: presence of
  `<AppDirs.config_dir>/.first-run-completed.json` recording the run.

`AutoBootstrap.decide()` returns one of `SKIP` (fully provisioned),
`ONBOARD_MINIMAL` (workspace fine, provider missing), or
`ONBOARD_FULL` (fresh machine). The Task 186 default router calls
`AutoBootstrap` before chat REPL launch.

Read before starting:

- 46-first-run-onboarding-wizard.md
- 80-first-run-bootstrap.md
- 186-default-chat-repl-on-bare-command.md
- 00-task-index.md

## Files

- Create `src/proseforge_agent/install/auto_trigger.py`.
- Modify `src/proseforge_agent/cli.py` to have the Task 186 bare-command
  router consult `AutoBootstrap.decide()` before launching the REPL.
- Modify `src/proseforge_agent/install/first_run.py` to accept a
  `mode: Literal["minimal", "full"]` argument on `FirstRunWizard.run(...)`.
- Add tests in `tests/test_first_run_auto_trigger.py`.
- Add fixtures under `tests/fixtures/first-run-auto-trigger/`:
  `configured_home/`, `fresh_home/`, `partial_home/`.

## Interfaces / Contracts

- `AutoBootstrap(app_dirs, config_loader, secret_reader).decide() -> BootstrapDecision`.
- `BootstrapDecision` fields: `verdict` (`SKIP` / `ONBOARD_MINIMAL` /
  `ONBOARD_FULL`), `reason` (str), `missing` (list[str]).
- `FirstRunWizard.run(mode="minimal"|"full", interactive=True, answers=None) -> WizardReport`
  — `answers` is an optional prerecorded dict for deterministic tests.
- The bare-command router (Task 186) treats `SKIP` → chat REPL,
  `ONBOARD_MINIMAL/FULL` → `FirstRunWizard.run(mode=…)` then chat REPL.
- On completion the wizard writes `.first-run-completed.json` to
  `AppDirs.config_dir` so subsequent runs skip onboarding.

## Data Flow

1. Bare `pf-agent` → `AutoBootstrap.decide()`.
2. `decide()` reads config, workspace, consent marker; never mutates.
3. Router branches on verdict.
4. Wizard writes provider config + workspace root + consent marker.
5. Router loops back to REPL launch with the fresh config.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_first_run_auto_trigger.py::test_decide_returns_skip_when_provider_and_workspace_ready`**

```python
def test_decide_returns_skip_when_provider_and_workspace_ready(tmp_path):
    (tmp_path / ".first-run-completed.json").write_text("{\"version\":1}", encoding="utf-8")
    decision = AutoBootstrap(
        app_dirs=FakeAppDirs(config_dir=tmp_path, data_dir=tmp_path),
        config_loader=lambda: AgentConfig(...),
        secret_reader=lambda name: "sk-fake",
    ).decide()
    assert decision.verdict == "SKIP"
```

- [ ] **Step 2: Run the targeted test and confirm failure.**

- [ ] **Step 3: Implement `AutoBootstrap` and wire into the Task 186 router.**

- [ ] **Step 4: Run the targeted test and confirm pass.**

- [ ] **Step 5: Add companion tests**

```text
test_decide_returns_onboard_full_on_fresh_home
test_decide_returns_onboard_minimal_when_workspace_ok_provider_missing
test_wizard_writes_first_run_completed_marker_on_success
test_router_launches_wizard_then_repl_on_first_run
test_router_never_prompts_when_marker_present_and_config_valid
test_decide_uses_env_var_override_PF_AGENT_SKIP_FIRST_RUN
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_first_run_auto_trigger.py -q
Remove-Item -Recurse -Force "$env:APPDATA/ProseForge Agent" -ErrorAction SilentlyContinue
pf-agent            # → wizard, then REPL
pf-agent            # → REPL directly
```

- [ ] **Step 7: Run full repository verification**

```powershell
python -m pytest -q
```

- [ ] **Step 8: Record commit boundary**

```powershell
git add src/proseforge_agent/install/auto_trigger.py src/proseforge_agent/install/first_run.py src/proseforge_agent/cli.py tests/test_first_run_auto_trigger.py tests/fixtures/first-run-auto-trigger
git commit -m "feat: auto-trigger first-run onboarding"
```

## Cross-Platform Notes

- Consent marker path resolves through `AppDirs.config_dir`, never
  hard-coded home paths.
- On Windows the marker must survive `%LOCALAPPDATA%` roaming assumptions —
  write it to `config_dir` (Roaming) not `data_dir` (Local).
- The env-var override `PF_AGENT_SKIP_FIRST_RUN=1` allows scripted CI
  environments to bypass onboarding without setting a marker on the machine.

## Failure Modes To Prove

- Corrupt consent marker (unparseable JSON) is treated as "no marker" and
  triggers full onboarding instead of a crash.
- A user who Ctrl-C's the wizard returns exit 130 and the marker is NOT
  written.
- `SKIP` decision never opens files under `data_dir` beyond reading.
- Missing secret storage backend does not raise; it is reported in
  `decision.missing` and drives `ONBOARD_MINIMAL`.

## Verification

```powershell
python -m pytest tests/test_first_run_auto_trigger.py -q
python -m pytest -q
```

## Acceptance

- Bare `pf-agent` on a fresh machine walks through wizard → REPL without any
  extra flags.
- Second `pf-agent` invocation lands directly in the REPL.
- The consent marker is versioned so we can migrate its shape later.

## Commit Boundary

Commit only the auto-trigger detector, the wizard mode flag, the tests, and
the router glue. Do not bundle the default REPL router change (Task 186 —
its commit already added the `_dispatch_bare_command` shell), the install
scripts (187), Docker packaging (192), or docs.
