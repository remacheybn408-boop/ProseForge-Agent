# Phase 09: Installation And Native Platforms

Dates: 2026-10-09 to 2026-10-23.

Goal: make ProseForge Agent installable and native on Windows, macOS, and Linux.

## Day 106: 2026-10-09, First-Run Onboarding

Primary objective: implement Task 41 for `pf-agent init`.

Verification:

```powershell
python -m pytest tests/test_first_run_onboarding.py -q
pf-agent init --dry-run
```

Acceptance: init creates portable config and workspace plan without machine-specific paths.

## Day 107: 2026-10-10, Installation Doctor

Primary objective: implement Task 42 for actionable diagnostics.

Verification:

```powershell
python -m pytest tests/test_installation_doctor.py -q
pf-agent doctor --json
```

Acceptance: doctor reports OS, Python, config, workspace, ProseForge root, provider keys, secret backend, encoding, and recovery steps.

## Day 108: 2026-10-11, Cross-Platform App Directories

Primary objective: implement Task 43 for native app dirs plus portable `.pf-agent` mode.

Verification:

```powershell
python -m pytest tests/test_app_dirs.py -q
pf-agent doctor --section app-dirs
```

Acceptance: Windows, macOS, and Linux directory rules are covered by tests.

## Day 109: 2026-10-12, Path, Encoding, And Terminal Support

Primary objective: implement Task 44 for shell quoting, UTF-8, and paths with spaces.

Verification:

```powershell
python -m pytest tests/test_platform_io.py -q
pf-agent doctor --section platform-io
```

Acceptance: Chinese text and paths with spaces survive command rendering and reports.

## Day 110: 2026-10-13, Native Secret Storage

Primary objective: implement Task 45 for Credential Manager, Keychain, Secret Service, and env fallback.

Verification:

```powershell
python -m pytest tests/test_native_secret_storage.py -q
pf-agent doctor --section secrets
```

Acceptance: provider keys are never printed and fallback warnings are visible.

## Day 111: 2026-10-14, Provider Setup Wizard

Primary objective: implement Task 46 for guided provider configuration.

Verification:

```powershell
python -m pytest tests/test_provider_setup_wizard.py -q
pf-agent provider setup --provider deepseek --dry-run
```

Acceptance: wizard writes provider profiles and stores secrets without exposing key values.

## Day 112: 2026-10-15, pip, pipx, And Source Installation

Primary objective: implement Task 47 for Python install channels.

Verification:

```powershell
python -m pytest tests/test_python_install_flows.py -q
python -m pip install -e .
pf-agent --help
```

Acceptance: editable install and console entrypoint work.

## Day 113: 2026-10-16, Standalone Binary Packaging

Primary objective: implement Task 48 for binary packaging manifests and smoke commands.

Verification:

```powershell
python -m pytest tests/test_binary_packaging.py -q
pf-agent package check --all-platforms --dry-run
```

Acceptance: package manifest covers Windows, macOS, and Linux artifact names and smoke checks.

## Day 114: 2026-10-17, Windows Native Support

Primary objective: implement Task 49.

Verification:

```powershell
python -m pytest tests/test_windows_native_support.py -q
pf-agent doctor --section windows-native-support
```

Acceptance: PowerShell, Windows Terminal, Credential Manager, long paths, spaces, and UTF-8 are covered.

## Day 115: 2026-10-18, macOS Native Support

Primary objective: implement Task 50.

Verification:

```powershell
python -m pytest tests/test_macos_native_support.py -q
pf-agent doctor --section macos-native-support
```

Acceptance: Keychain, Application Support, Caches, Logs, zsh, and package metadata are covered.

## Day 116: 2026-10-19, Linux Native Support

Primary objective: implement Task 51.

Verification:

```powershell
python -m pytest tests/test_linux_native_support.py -q
pf-agent doctor --section linux-native-support
```

Acceptance: XDG, Secret Service fallback, terminal encoding, systemd user-service notes, and local model endpoints are covered.

## Day 117: 2026-10-20, Shell Integration, Upgrade, And Uninstall

Primary objective: implement Tasks 52-54 as one install lifecycle gate.

Verification:

```powershell
python -m pytest tests/test_shell_completions_launchers.py tests/test_upgrade_migration_backup.py tests/test_uninstall_data_retention.py -q
pf-agent uninstall --dry-run
```

Acceptance: completions, migration backup, and uninstall data-retention choices are tested.

## Day 118: 2026-10-21, Offline Models, Local Service, Personas, And Support Bundle

Primary objective: implement Tasks 55-58.

Verification:

```powershell
python -m pytest tests/test_offline_local_model_setup.py tests/test_local_agent_service_api.py tests/test_agent_profiles_personas.py tests/test_support_bundle.py -q
pf-agent support bundle --dry-run
```

Acceptance: offline providers, local service API, agent profiles, and redacted diagnostics are available.

## Day 119: 2026-10-22, Native QA Matrix

Primary objective: implement Task 59.

Verification:

```powershell
python -m pytest tests/test_native_qa_matrix.py -q
pf-agent qa native-matrix --write-report
```

Acceptance: Windows, macOS, and Linux each require install, init, doctor, chat, provider setup, paths, secrets, upgrade, and uninstall evidence.

## Day 120: 2026-10-23, Complete Agent Release Gate

Primary objective: implement Task 60 and close the complete-agent plan.

Verification:

```powershell
python -m pytest -q
pf-agent release check --complete-agent --write-report
```

Acceptance: release blocks unless writing workflow, chat, provider certification, memory, install, native QA, diagnostics, and docs all pass.
