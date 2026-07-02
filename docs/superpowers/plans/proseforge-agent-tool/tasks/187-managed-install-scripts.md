# Task 187: Managed Install Scripts / 一键安装脚本

## Goal

Ship two managed install scripts — `scripts/install.sh` (Bash) and
`scripts/install.ps1` (PowerShell) — so an ordinary user with **no Python
knowledge** can install ProseForge Agent with one shell line:

```bash
curl -fsSL https://raw.githubusercontent.com/<org>/ProseForge-Agent/main/scripts/install.sh | bash
```

```powershell
iex (irm https://raw.githubusercontent.com/<org>/ProseForge-Agent/main/scripts/install.ps1)
```

The scripts detect / install `uv` (or fall back to `pipx`), ensure Python
3.10+, install `proseforge-agent` from PyPI (Task 189) or from a Git ref, and
register `pf-agent` on the user's PATH.

## Agent Product Requirement

Every current "just works" AI agent CLI (Hermes, Codex, Claude Code, Aider)
ships a one-line installer. It is table stakes for non-developer users.
Without it, users must know `pipx`, virtualenv, and PATH — the exact things
this project is trying to hide.

## Architecture Notes

Prefer `uv` (fast, hermetic, handles Python bootstrapping) with a `pipx`
fallback for machines where uv is not installable. Refuse to run inside an
already-active virtualenv (unless `--allow-venv` is passed) because that
almost always yields the "installed but not on PATH" symptom.

Both scripts share the same phases; only OS-specific commands differ:

1. Preflight (check permissions, detect existing pf-agent, refuse root install
   on Linux unless `--system` is passed).
2. Ensure Python 3.10+.
3. Ensure a package manager (uv preferred, pipx fallback).
4. Install `proseforge-agent` (default: latest PyPI; opt-in: `--git <ref>`).
5. Ensure the install target dir (`~/.local/bin` on POSIX,
   `%LOCALAPPDATA%\Programs\ProseForge Agent` on Windows) is on PATH.
6. Run `pf-agent doctor --format json` to prove the install; print a green
   "Next: `pf-agent`" line on success.

Failures are actionable: each phase prints a one-line remediation
(`re-run with --uv` / `install Xcode CLT` / `enable long paths`).

Read before starting:

- 44-cross-platform-app-directories.md
- 47-pip-pipx-source-installation.md
- 48-standalone-binary-packaging.md
- 183-pypi-publish.md
- 00-task-index.md

## Files

- Create `scripts/install.sh` (Bash, POSIX-portable, tested with `sh -n` and
  `shellcheck` in CI).
- Create `scripts/install.ps1` (PowerShell 5.1 compatible, tested with
  `PSScriptAnalyzer`).
- Create `scripts/_install_lib.sh` (shared helpers: `log`, `err`, `have`,
  `detect_os`).
- Create `src/proseforge_agent/install/installer_scripts.py` — pure-Python
  planner that produces the exact argv the scripts execute, so tests can
  assert phase order without running shell.
- Add tests in `tests/test_managed_install_scripts.py`.
- Add fixtures under `tests/fixtures/managed-install-scripts/`
  (`darwin_arm64.env`, `windows_amd64.env`, `linux_x64.env` sample).

## Interfaces / Contracts

- `ManagedInstallPlanner(os_name, arch, existing: dict[str, bool]).plan(
  package: str = "proseforge-agent", ref: str | None = None,
  system: bool = False, allow_venv: bool = False) -> InstallPlan`.
- `InstallPlan.phases` — ordered list of `InstallPhase(name, command,
  optional, remediation)`; every phase reports a stable name (`preflight /
  ensure_python / ensure_manager / install_package / register_path /
  post_verify`).
- CLI mirror: `pf-agent install script --emit sh` and `--emit ps1` write the
  scripts to stdout so downstream release tools can package them without
  reading the repo.

## Data Flow

1. Script starts → sources `_install_lib.sh` (or the PS module).
2. Preflight: check `--help / --version`, `--git <ref>`, `--system`,
   `--allow-venv`, `--uv/--pipx`, `--dry-run`. `--dry-run` prints the
   planned commands and exits 0.
3. Ensure Python: if missing, install via `uv python install 3.11`
   (POSIX) or the winget package `Python.Python.3.11` (Windows).
4. Ensure manager: `uv --version` else `pipx --version` else install uv.
5. Install: `uv tool install proseforge-agent` (or
   `pipx install proseforge-agent`); with `--git <ref>` use
   `uv tool install git+…` / `pipx install git+…`.
6. Register PATH: append to `~/.bashrc` / `~/.zshrc` on POSIX; use
   `setx PATH` on Windows.
7. Post-verify: run `pf-agent doctor --format json`; fail if any check ≠ ok.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_managed_install_scripts.py::test_plan_orders_phases_and_uses_uv_when_available`**

```python
def test_plan_orders_phases_and_uses_uv_when_available():
    plan = ManagedInstallPlanner("linux", "x64", {"uv": True, "python311": True}).plan()
    names = [p.name for p in plan.phases]
    assert names == ["preflight", "ensure_python", "ensure_manager",
                     "install_package", "register_path", "post_verify"]
    assert any("uv tool install proseforge-agent" in " ".join(p.command) for p in plan.phases)
```

- [ ] **Step 2: Run the targeted test and confirm failure.**

- [ ] **Step 3: Implement `ManagedInstallPlanner` in
  `src/proseforge_agent/install/installer_scripts.py` and the two shell
  scripts.**

- [ ] **Step 4: Run the targeted test and confirm pass.**

- [ ] **Step 5: Add companion tests**

```text
test_plan_falls_back_to_pipx_when_uv_missing
test_plan_refuses_to_install_inside_active_venv_without_flag
test_plan_uses_git_ref_when_git_flag_supplied
test_plan_registers_path_on_windows_via_setx
test_plan_dry_run_command_is_pure_and_writes_no_files
test_shell_script_passes_shellcheck
test_powershell_script_passes_psscriptanalyzer
test_cli_emit_writes_script_to_stdout_verbatim
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_managed_install_scripts.py -q
bash -n scripts/install.sh
pwsh -Command "Invoke-ScriptAnalyzer -Path scripts/install.ps1"   # optional
python -m proseforge_agent.cli install script --emit sh | head -5
```

- [ ] **Step 7: Run full repository verification**

```powershell
python -m pytest -q
```

- [ ] **Step 8: Record commit boundary**

```powershell
git add scripts/install.sh scripts/install.ps1 scripts/_install_lib.sh src/proseforge_agent/install/installer_scripts.py tests/test_managed_install_scripts.py tests/fixtures/managed-install-scripts
git commit -m "feat: add managed install scripts"
```

## Cross-Platform Notes

- Bash script must be POSIX-portable (no `[[ ]]`, no `$'...'`), start with
  `set -euo pipefail`, and support Bash 3.2 (macOS default).
- PowerShell script must be PS 5.1 compatible — no `??`, no `?:`,
  no `-ErrorAction Ignore` (use `SilentlyContinue`).
- Windows install target: `%LOCALAPPDATA%\Programs\ProseForge Agent`.
  POSIX target: `~/.local/bin`.
- Use `pathlib.Path.expanduser()` in the planner; never hard-code `/home/*`
  or `C:\Users\*`.

## Failure Modes To Prove

- Running inside an active venv aborts with an actionable error unless
  `--allow-venv`.
- A machine without Python 3.10+ triggers the `ensure_python` phase and, on
  systems where install is not possible (offline, no admin), fails with a
  clear remediation.
- With `--dry-run`, no file is written and no command is executed.
- With `--git <ref>`, the install phase uses the Git URL and pins the ref.
- Neither the report nor any log line ever prints an access token.

## Verification

```powershell
python -m pytest tests/test_managed_install_scripts.py -q
python -m proseforge_agent.cli install script --emit sh --dry-run
python -m pytest -q
```

## Acceptance

- The Bash and PowerShell scripts run end-to-end on a fresh machine and
  register `pf-agent` on PATH.
- Both scripts pass `shellcheck` / `PSScriptAnalyzer` in CI.
- The `ManagedInstallPlanner` output is the single source of truth for the
  ordered phases; drift between planner and shell scripts is caught by
  golden tests.

## Commit Boundary

Commit only the scripts, the planner, and their tests. Do not bundle the
default-REPL change (Task 186), the PyPI publish execution (Task 189),
Docker packaging (Task 192), or docs (193/194).
