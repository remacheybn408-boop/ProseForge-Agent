# Task 76: pf-agent setup Guided Installation Wizard

## Goal

Add a product-grade guided setup command, `pf-agent setup`, that turns the install pieces from Tasks 41-55 into one repeatable first-use flow.

The setup flow must make this path work for a new user:

```powershell
pipx install proseforge-agent
pf-agent setup --quick
pf-agent doctor
pf-agent chat
```

It must also support zero-key offline validation:

```powershell
pf-agent setup --minimal
pf-agent chat --provider fake --message "写一个小说开头"
```

## Agent Product Requirement

Users should not have to understand app directories, provider profiles, key storage, shell completions, doctor checks, or fake-provider smoke tests before they can use the agent. The setup command is the product entry ramp: it diagnoses the environment, configures a workspace and provider, stores secrets safely, runs non-blocking validation, and prints concrete next steps.

This card intentionally assembles existing install subsystems instead of rewriting them:

- First-run workspace and app dirs from Tasks 41 and 43.
- Installation doctor from Task 42.
- Native secret storage from Task 45.
- Provider setup from Task 46.
- Package/source detection from Task 47.
- Shell completions from Task 52.
- Upgrade/backup and repair primitives from Task 53.
- Offline local/fake provider behavior from Task 55.

## Architecture Notes

Create a focused `setup` package that orchestrates existing install helpers through dependency injection. The wizard owns mode selection, prompts, config merge/backup, summary rendering, first-run bootstrap checks, and safe failure handling; low-level provider, doctor, secret, app-dir, and shell modules remain the source of truth.

`pf-agent setup` must follow the existing argparse/report style in `src/proseforge_agent/cli.py`. Do not introduce Typer, Click, or a second CLI framework.

Failures in provider ping, keyring, shell completion, ProseForge engine discovery, and network checks are warnings, not setup blockers. Minimal/fake mode must remain available even when every external dependency is missing.

## Files

- Create `src/proseforge_agent/setup/__init__.py`
- Create `src/proseforge_agent/setup/modes.py`
- Create `src/proseforge_agent/setup/wizard.py`
- Create `src/proseforge_agent/setup/config_generator.py`
- Create `src/proseforge_agent/setup/first_run.py`
- Create `src/proseforge_agent/setup/recovery.py`
- Create `src/proseforge_agent/setup/summary.py`
- Modify `src/proseforge_agent/cli.py`
- Test with `tests/setup/test_setup_minimal.py`
- Test with `tests/setup/test_setup_config_generation.py`
- Test with `tests/setup/test_setup_reconfigure.py`
- Test with `tests/setup/test_setup_add_provider.py`
- Test with `tests/setup/test_setup_first_run.py`
- Test with `tests/setup/test_setup_non_interactive.py`

## Interfaces / Contracts

`SetupMode`:

```python
class SetupMode(str, Enum):
    QUICK = "quick"
    FULL = "full"
    MINIMAL = "minimal"
    NON_INTERACTIVE = "non_interactive"
```

`ProviderSetupResult`:

```python
@dataclass
class ProviderSetupResult:
    name: str
    enabled: bool
    configured: bool
    status: Literal["ok", "skip", "fail", "warn"]
    latency_ms: int | None = None
    reason: str | None = None
```

`SetupResult`:

```python
@dataclass
class SetupResult:
    completed: bool
    mode: str
    config_path: Path
    workspace_path: Path
    providers: list[ProviderSetupResult]
    warnings: list[str]
    errors: list[str]
    next_steps: list[str]
```

Required CLI flags:

```powershell
pf-agent setup --quick
pf-agent setup --full
pf-agent setup --minimal
pf-agent setup --non-interactive
pf-agent setup --reconfigure
pf-agent setup --add-provider
pf-agent setup --add-provider deepseek
pf-agent setup --skip-provider-test
pf-agent setup --no-shell
pf-agent setup --repair
pf-agent setup --print-config
```

Provider ordering for quick mode:

1. DeepSeek
2. Qwen
3. GLM
4. Doubao
5. OpenAI
6. Anthropic
7. Gemini
8. Fake

Default provider selection:

- If `DEEPSEEK_API_KEY` exists, default to DeepSeek.
- Else if `OPENAI_API_KEY` exists, default to OpenAI.
- Else default to Fake minimal mode.
- Always keep Fake enabled as fallback.

Secret storage contract:

- Never write raw API keys to `config.yaml`.
- Prefer native keyring/keychain references, e.g. `keychain://proseforge-agent/deepseek`.
- If keyring is unavailable, store an environment reference, e.g. `env://DEEPSEEK_API_KEY`.
- Only write `.env` when the user explicitly allows it; ensure `.env` is ignored or print a safety warning.

Config generation contract:

- Write the effective config to the resolved app config path.
- If config exists, create `config.yaml.bak-YYYYMMDD-HHMMSS` before writing.
- Merge user-owned fields where safe; if merge cannot be proven safe, backup and rewrite with a warning.
- Minimal mode must include `setup.completed = true`, Fake provider enabled/configured, and a workspace path.

Workspace contract:

- Default workspace path: `~/.proseforge-agent/workspace`.
- Create or repair these directories without deleting existing content: `projects`, `drafts`, `exports`, `logs`, `cache`, `tmp`, `backups`.
- Reconfigure and repair must not delete drafts, memory, `agent.db`, rules, config backups, or provider secrets.

First-run bootstrap contract:

- For `pf-agent`, `pf-agent chat`, `pf-agent daily-workbook`, `pf-agent chapter draft`, and `pf-agent provider list`, detect missing/incomplete setup.
- In interactive terminals, offer to enter setup.
- In CI/non-interactive contexts, return a clear error code and print:

```text
ProseForge Agent 尚未完成初始化。

推荐：
  pf-agent setup --quick

零配置验证：
  pf-agent setup --minimal

手动检查：
  pf-agent doctor
```

## Data Flow

1. Resolve mode from flags and environment.
2. Run doctor-style environment detection for Python, OS, install source, writable paths, keyring, network, existing config, workspace, ProseForge engine, and shell.
3. Choose default provider from env keys and mode rules.
4. Store API keys through `SecretStore`; write only secret references to config.
5. Create or repair workspace directories without deleting user data.
6. Detect ProseForge engine from `PROSEFORGE_ROOT`, sibling path, user input, or skip with `engine.enabled = false`.
7. Backup and merge/write config.
8. Run provider ping unless `--skip-provider-test`; record failures as warnings.
9. Register shell completion unless `--no-shell`; record failures as warnings.
10. Run doctor summary.
11. Render a setup summary with warnings, next commands, and no secret values.

## TDD Steps

- [ ] **Step 1: Write failing minimal setup test `tests/setup/test_setup_minimal.py::test_minimal_setup_creates_fake_provider_workspace_and_config`**

```python
def test_minimal_setup_creates_fake_provider_workspace_and_config(tmp_path):
    result = SetupWizard(root=tmp_path).run(mode=SetupMode.MINIMAL)
    config_text = result.config_path.read_text(encoding="utf-8")
    assert result.completed is True
    assert result.workspace_path.exists()
    assert "fake" in config_text
    assert "completed: true" in config_text
    assert result.errors == []
```

- [ ] **Step 2: Run the targeted minimal setup test and confirm failure**

```powershell
python -m pytest tests/setup/test_setup_minimal.py::test_minimal_setup_creates_fake_provider_workspace_and_config -q
```

Expected: FAIL because `proseforge_agent.setup` and `SetupWizard` do not exist.

- [ ] **Step 3: Implement minimal setup skeleton**

Implement `SetupMode`, `SetupResult`, `ProviderSetupResult`, workspace directory creation, minimal Fake provider config generation, summary rendering, and `pf-agent setup --minimal`.

- [ ] **Step 4: Run the targeted minimal setup test and CLI smoke**

```powershell
python -m pytest tests/setup/test_setup_minimal.py::test_minimal_setup_creates_fake_provider_workspace_and_config -q
python -m proseforge_agent.cli setup --minimal
python -m proseforge_agent.cli chat --provider fake --message "hello"
```

Expected: targeted test passes; setup exits 0; fake chat exits 0.

- [ ] **Step 5: Add config generation and secret-redaction tests**

Add:

```text
test_config_generator_never_writes_plaintext_api_key
test_existing_config_is_backed_up_before_reconfigure
test_print_config_outputs_key_ref_only
test_config_merge_preserves_unknown_user_fields
```

Run:

```powershell
python -m pytest tests/setup/test_setup_config_generation.py -q
```

Expected: PASS with no raw `sk-test` value in generated config or summary output.

- [ ] **Step 6: Add provider setup tests**

Add:

```text
test_add_provider_appends_deepseek_without_resetting_fake
test_provider_ping_failure_is_warning_not_setup_failure
test_skip_provider_test_marks_provider_unverified
test_quick_mode_prefers_deepseek_env_key_then_openai_then_fake
```

Run:

```powershell
python -m pytest tests/setup/test_setup_add_provider.py -q
python -m proseforge_agent.cli setup --add-provider deepseek --skip-provider-test
```

Expected: tests pass; CLI exits 0 and keeps Fake fallback.

- [ ] **Step 7: Add reconfigure and repair tests**

Add:

```text
test_reconfigure_preserves_drafts_memory_and_agent_db
test_reconfigure_creates_config_backup
test_repair_recreates_missing_workspace_directories
test_repair_fixes_setup_completed_flag_without_deleting_data
```

Run:

```powershell
python -m pytest tests/setup/test_setup_reconfigure.py -q
```

Expected: tests pass and user data files remain unchanged.

- [ ] **Step 8: Add first-run bootstrap tests**

Add:

```text
test_chat_without_setup_prints_setup_guidance
test_daily_workbook_without_setup_prints_setup_guidance
test_non_interactive_bootstrap_returns_error_without_prompt
test_interactive_bootstrap_can_enter_setup
```

Run:

```powershell
python -m pytest tests/setup/test_setup_first_run.py -q
```

Expected: tests pass; non-interactive path prints `pf-agent setup --quick` and `pf-agent setup --minimal`.

- [ ] **Step 9: Add non-interactive tests**

Add:

```text
test_non_interactive_uses_env_and_defaults_without_prompt
test_non_interactive_without_keys_enables_fake_provider
test_non_interactive_json_summary_is_machine_readable
test_non_interactive_missing_engine_is_warning_not_failure
```

Run:

```powershell
python -m pytest tests/setup/test_setup_non_interactive.py -q
python -m proseforge_agent.cli setup --non-interactive
```

Expected: tests pass; CLI exits 0 without prompting.

- [ ] **Step 10: Run full setup verification**

```powershell
python -m pytest tests/setup -q
python -m proseforge_agent.cli setup --minimal
python -m proseforge_agent.cli doctor
python -m proseforge_agent.cli chat --provider fake --message "hello"
python -m proseforge_agent.cli setup --print-config
```

Expected: tests and commands pass; print-config does not leak secrets.

- [ ] **Step 11: Run full repository verification**

```powershell
python -m pytest -q
```

Expected: full suite passes.

- [ ] **Step 12: Record commit boundary**

```powershell
git add src/proseforge_agent/setup src/proseforge_agent/cli.py tests/setup
git commit -m "feat: add guided setup wizard"
```

If implementation also requires narrow install-helper changes, include only those files in the same commit and document why in closeout.

## Cross-Platform Notes

- All examples must avoid machine-specific absolute paths.
- Paths with spaces and Chinese text must round-trip on Windows, macOS, and Linux.
- PowerShell, Bash, Zsh, Fish, and unknown shell detection must degrade safely.
- No setup report may print raw API keys, tokens, passwords, or secret values.
- Provider and network tests must be injectable/offline in unit tests.

## Failure Modes To Prove

- Invalid provider key records `fail` or `warn` but setup exits 0 with Fake fallback available.
- Keyring unavailable falls back to env var reference and reports the weaker backend.
- ProseForge engine missing records a warning and writes `engine.enabled = false`.
- Shell completion registration failure records a warning and prints manual install guidance.
- Reconfigure preserves existing workspace data, drafts, memory, `agent.db`, rules, backups, and secrets.
- Print-config outputs key references only.
- Non-interactive/CI never opens a prompt.

## Verification

```powershell
python -m pytest tests/setup -q
python -m proseforge_agent.cli setup --minimal
python -m proseforge_agent.cli doctor
python -m proseforge_agent.cli chat --provider fake --message "hello"
python -m proseforge_agent.cli setup --non-interactive
python -m proseforge_agent.cli setup --add-provider deepseek --skip-provider-test
python -m proseforge_agent.cli setup --reconfigure --minimal
python -m proseforge_agent.cli setup --print-config
python -m pytest -q
```

## Acceptance

- `pf-agent setup --minimal` creates a config and workspace, enables Fake provider, requires no API key, exits 0, and allows Fake chat.
- `pf-agent setup --non-interactive` uses env/defaults, never prompts, exits 0 without keys, and emits a summary.
- `pf-agent setup --add-provider deepseek` appends provider config without resetting workspace or Fake fallback.
- `pf-agent setup --reconfigure` backs up existing config and does not delete user data.
- `pf-agent setup --repair` restores missing setup fields/directories without deleting user data.
- `pf-agent setup --print-config` never leaks raw API keys.
- First-run bootstrap guides users into setup instead of failing with an unexplained stack trace.

## Commit Boundary

Commit only setup wizard code, narrow CLI wiring, setup tests, and required fixtures:

```powershell
git add src/proseforge_agent/setup src/proseforge_agent/cli.py tests/setup
git commit -m "feat: add guided setup wizard"
```

Do not modify provider adapters, rewrite install modules wholesale, or change unrelated docs in this task.
