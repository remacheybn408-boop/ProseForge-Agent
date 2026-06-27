# Installation And Native Platform Architecture

## Goal

ProseForge Agent must install and run natively on Windows, macOS, and Linux. A user should not need to edit source files or know the developer's machine paths.

## Supported Install Channels

| Channel | Audience | Command Shape |
| --- | --- | --- |
| Source checkout | Contributors and early testers. | `python -m pip install -e .` |
| pip / pipx package | Python users. | `pipx install proseforge-agent` |
| Standalone binary | Non-Python users. | `pf-agent.exe`, `pf-agent`, or app bundle launcher. |
| Native package metadata | Later distribution. | winget, Homebrew, apt/rpm package recipes. |

## First Run Flow

```text
pf-agent init
  -> detect OS
  -> detect Python and terminal encoding
  -> choose app data directory
  -> ask for or detect PROSEFORGE_ROOT
  -> create config
  -> create workspace
  -> choose provider setup path
  -> run doctor
  -> write first-run report
```

## Cross-Platform Directory Rules

| Data | Windows | macOS | Linux |
| --- | --- | --- | --- |
| Config | `%APPDATA%\\ProseForgeAgent\\config.yaml` | `~/Library/Application Support/ProseForgeAgent/config.yaml` | `${XDG_CONFIG_HOME:-~/.config}/proseforge-agent/config.yaml` |
| Data | `%LOCALAPPDATA%\\ProseForgeAgent` | `~/Library/Application Support/ProseForgeAgent` | `${XDG_DATA_HOME:-~/.local/share}/proseforge-agent` |
| Cache | `%LOCALAPPDATA%\\ProseForgeAgent\\Cache` | `~/Library/Caches/ProseForgeAgent` | `${XDG_CACHE_HOME:-~/.cache}/proseforge-agent` |
| Logs | `%LOCALAPPDATA%\\ProseForgeAgent\\Logs` | `~/Library/Logs/ProseForgeAgent` | `${XDG_STATE_HOME:-~/.local/state}/proseforge-agent/logs` |

Project-local workspace remains supported through `.pf-agent/` when the user chooses portable mode.

## Secret Storage

API keys must not be stored in plain config by default.

| Platform | Preferred Store | Fallback |
| --- | --- | --- |
| Windows | Windows Credential Manager | Environment variable |
| macOS | Keychain | Environment variable |
| Linux | Secret Service / libsecret | Environment variable |

The fallback must be visible in `pf-agent doctor` so users know when secrets are less protected.

## Native Terminal Support

Required behaviors:

- PowerShell and Windows Terminal support UTF-8 output.
- CMD receives simple ASCII fallback where needed.
- macOS Terminal and iTerm work with UTF-8 paths and Chinese text.
- Linux terminals work with UTF-8, XDG directories, and symlinks.
- All commands support paths containing spaces.
- All examples avoid hard-coded drive letters.

## Shell Integration

Installable shell completions:

- PowerShell profile snippet.
- Bash completion.
- Zsh completion.
- Fish completion.

Launch helpers:

- `pf-agent` console command.
- `pf-agent chat` interactive REPL.
- Optional background service launcher for local API mode.

## Doctor Checks

`pf-agent doctor` must report:

- OS and architecture.
- Python version.
- package version.
- config path.
- workspace path.
- ProseForge root status.
- provider profile status.
- secret store backend.
- terminal encoding.
- path writability.
- optional binary packaging status.
- next recovery command for each failure.

## Upgrade And Uninstall

Upgrade must preserve:

- config files.
- workspaces.
- chats.
- memory stores.
- provider certification records.
- workflow runs.

Uninstall must offer:

- remove binaries only.
- remove shell integration.
- remove cache/logs.
- preserve or delete user data with an explicit confirmation.

## Acceptance Criteria

- A user can install from source on Windows, macOS, and Linux.
- `pf-agent init` creates a working config without machine-specific paths.
- `pf-agent doctor` gives platform-specific recovery steps.
- `pf-agent chat` starts on all three platforms.
- Provider keys can be stored through native secret backends or environment variables.
- Packaging checks prove command entry points work after install.
