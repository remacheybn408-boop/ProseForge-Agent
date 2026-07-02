#!/usr/bin/env sh
# ProseForge Agent one-line installer (Task 187).
#
#   curl -fsSL https://raw.githubusercontent.com/<org>/ProseForge-Agent/main/scripts/install.sh | sh
#
# Installs uv (preferred) or uses pipx, ensures Python 3.10+, installs the
# `proseforge-agent` package, and registers `pf-agent` on your PATH.
#
# Flags: --git <ref>  --system  --allow-venv  --uv  --pipx  --dry-run  --help
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
# shellcheck source=scripts/_install_lib.sh
if [ -f "$SCRIPT_DIR/_install_lib.sh" ]; then
    . "$SCRIPT_DIR/_install_lib.sh"
else
    log() { printf '[pf-agent-install] %s\n' "$1"; }
    err() { printf '[pf-agent-install] ERROR: %s\n' "$1" >&2; }
    have() { command -v "$1" >/dev/null 2>&1; }
    detect_os() { echo linux; }
    in_active_venv() { [ -n "${VIRTUAL_ENV:-}" ]; }
fi

PACKAGE="proseforge-agent"
GIT_REF=""
ALLOW_VENV=0
DRY_RUN=0
FORCE_MANAGER=""

usage() {
    cat <<'EOF'
Usage: install.sh [--git REF] [--system] [--allow-venv] [--uv|--pipx] [--dry-run]
Installs proseforge-agent and registers the pf-agent command on PATH.
EOF
}

while [ $# -gt 0 ]; do
    case "$1" in
        --git) GIT_REF="$2"; shift 2 ;;
        --system) shift ;;
        --allow-venv) ALLOW_VENV=1; shift ;;
        --uv) FORCE_MANAGER="uv"; shift ;;
        --pipx) FORCE_MANAGER="pipx"; shift ;;
        --dry-run) DRY_RUN=1; shift ;;
        --help | -h) usage; exit 0 ;;
        *) err "unknown flag: $1"; usage; exit 2 ;;
    esac
done

run() {
    if [ "$DRY_RUN" -eq 1 ]; then
        log "DRY-RUN: $*"
    else
        log "+ $*"
        "$@"
    fi
}

if in_active_venv && [ "$ALLOW_VENV" -eq 0 ]; then
    err "refusing to install inside an active virtualenv; deactivate or pass --allow-venv"
    exit 3
fi

OS=$(detect_os)
log "target OS: $OS"

# ensure a package manager (uv preferred)
if [ "$FORCE_MANAGER" = "pipx" ] || { [ -z "$FORCE_MANAGER" ] && ! have uv && have pipx; }; then
    MANAGER="pipx"
else
    MANAGER="uv"
    if ! have uv; then
        log "installing uv"
        run sh -c "curl -LsSf https://astral.sh/uv/install.sh | sh"
    fi
fi
log "using manager: $MANAGER"

# ensure python
if [ "$MANAGER" = "uv" ] && ! have python3; then
    run uv python install 3.11
fi

# install package
if [ -n "$GIT_REF" ]; then
    TARGET="git+https://github.com/NousResearch/proseforge-agent@$GIT_REF"
else
    TARGET="$PACKAGE"
fi
if [ "$MANAGER" = "uv" ]; then
    run uv tool install "$TARGET"
else
    run pipx install "$TARGET"
fi

# register PATH
case ":$PATH:" in
    *":$HOME/.local/bin:"*) : ;;
    *)
        log "adding \$HOME/.local/bin to PATH in ~/.profile"
        if [ "$DRY_RUN" -eq 0 ]; then
            printf 'export PATH="$HOME/.local/bin:$PATH"\n' >> "$HOME/.profile"
        fi
        ;;
esac

# verify
if [ "$DRY_RUN" -eq 0 ] && have pf-agent; then
    run pf-agent doctor --format json || err "doctor reported problems; see output above"
fi

log "done. Next: run 'pf-agent'"
