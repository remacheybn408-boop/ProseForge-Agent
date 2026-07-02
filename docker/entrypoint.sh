#!/usr/bin/env sh
# ProseForge Agent container entrypoint (Task 192).
# Runs the early bootstrap, then delegates all args to pf-agent.
set -eu

# Ensure the mounted workspace is writable by the pfagent user.
if [ -d /data ] && [ ! -w /data ]; then
    echo "[entrypoint] warning: /data is not writable by $(id -un)" >&2
fi

python -m proseforge_agent._bootstrap >/dev/null 2>&1 || true

exec pf-agent "$@"
