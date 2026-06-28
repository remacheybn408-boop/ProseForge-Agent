# Task 52: Shell Completions And Launchers

## Goal

Install and remove PowerShell, Bash, Zsh, and Fish completions plus launch helpers.

## Agent Product Requirement

Native command experience includes completion and predictable launch behavior.

## Architecture Notes

`shell` renders completion scripts and profile snippets for each supported shell and plans their install/uninstall. Writing to a user profile is a `system_write` action and must be explicit; rendering a script is read-only. It reuses `platform_io` (Task 44) for shell quoting/paths and reports its actions through the doctor (Task 42). It never edits a profile without an explicit install request.

Read before starting:

- ../architecture/02-system-architecture.md
- ../architecture/09-installation-and-native-platforms.md (Shell Integration)
- 00-task-index.md

## Files

- Create `src/proseforge_agent/install/shell.py`
- Create `tests/test_shell_completions_launchers.py`
- Create `tests/fixtures/shell-completions-and-launchers/expected_snippets.json`

## Interfaces / Contracts

- `ShellCompletionRenderer().render(shell) -> CompletionScript` for `powershell`, `bash`, `zsh`, `fish`.
- `CompletionScript` fields: `shell`, `script_text`, `install_target` (logical path), `install_action` (`system_write`).
- `ShellInstaller(platform_io).plan(shell, install: bool) -> InstallPlan`; rendering is read-only, installing requires the `system_write` permission.
- An unknown shell raises `ConfigurationError`.

## Data Flow

1. Select the shell template.
2. Render the completion script and profile snippet.
3. Resolve the logical install target via `platform_io`.
4. Produce an install or uninstall plan marked `system_write`.
5. Return the script/plan without writing unless install is requested.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_shell_completions_launchers.py::test_render_powershell_completion_is_read_only_and_targets_profile`**

```python
def test_render_powershell_completion_is_read_only_and_targets_profile():
    script = ShellCompletionRenderer().render(shell="powershell")
    assert "pf-agent" in script.script_text
    assert script.install_action == "system_write"
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/test_shell_completions_launchers.py::test_render_powershell_completion_is_read_only_and_targets_profile -q
```

Expected: FAIL because `ShellCompletionRenderer` and `CompletionScript` are missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement `ShellCompletionRenderer`, `CompletionScript`, `ShellInstaller`, and `InstallPlan`.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/test_shell_completions_launchers.py::test_render_powershell_completion_is_read_only_and_targets_profile -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

```text
test_bash_zsh_fish_completions_render
test_install_requires_system_write_permission
test_uninstall_plan_removes_only_managed_snippet
test_unknown_shell_raises_configuration_error
test_install_target_uses_no_absolute_machine_path
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_shell_completions_launchers.py -q
pf-agent completions show --shell powershell
```

Expected: tests pass and the command prints a completion script without modifying any profile.

- [ ] **Step 7: Run cross-platform contract check**

```powershell
python -m pytest tests/test_shell_completions_launchers.py -q
```

Expected: PASS for the simulated PowerShell, Bash, Zsh, and Fish cases in the test file.

- [ ] **Step 8: Record commit boundary**

```powershell
git add src/proseforge_agent/install/shell.py tests/test_shell_completions_launchers.py tests/fixtures/shell-completions-and-launchers
git commit -m "feat: add shell completions"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Cross-Platform Notes

- Completions cover PowerShell, Bash, Zsh, and Fish.
- Install targets are logical paths resolved per platform, never hard-coded.
- Snippets are UTF-8 and copy-pasteable.

## Failure Modes To Prove

- Rendering never writes to a profile.
- Installing without `system_write` permission is refused.
- Uninstall removes only the managed snippet, not the whole profile.
- Unknown shell raises `ConfigurationError`.

## Verification

```powershell
python -m pytest tests/test_shell_completions_launchers.py -q
pf-agent completions show --shell powershell
```

## Acceptance

- Completion scripts render for all supported shells.
- Install/uninstall are explicit and permission-gated.
- Rendering is read-only.
- No machine-specific absolute paths in targets.

## Commit Boundary

Commit only shell-integration files and tests after verification passes. Do not edit user profiles in tests.
