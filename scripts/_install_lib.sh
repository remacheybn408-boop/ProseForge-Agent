#!/usr/bin/env sh
# Shared helpers for the ProseForge Agent managed install script (Task 187).
# POSIX sh only: no bashisms, safe under `set -eu`.

log() {
    printf '[pf-agent-install] %s\n' "$1"
}

err() {
    printf '[pf-agent-install] ERROR: %s\n' "$1" >&2
}

have() {
    command -v "$1" >/dev/null 2>&1
}

detect_os() {
    # Prints one of: windows macos linux
    case "$(uname -s 2>/dev/null || echo unknown)" in
        Darwin) echo macos ;;
        Linux) echo linux ;;
        MINGW* | MSYS* | CYGWIN*) echo windows ;;
        *) echo linux ;;
    esac
}

in_active_venv() {
    # Returns success (0) when a virtualenv is active.
    [ -n "${VIRTUAL_ENV:-}" ]
}
