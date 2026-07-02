# Running ProseForge Agent in Docker

No Python setup required — run the agent in a container.

## Linux / macOS

```bash
docker compose up            # builds the image and prints help
docker compose run --rm pf-agent chat --message "draft an opening" --provider fake
docker compose exec pf-agent pf-agent --version
```

Workspace data persists in `./data`; put `.env` and provider YAML in `./config`.

## Windows (Docker Desktop)

```powershell
docker compose -f docker-compose.windows.yml up
```

The Windows compose uses a **named volume** for `/data` because NTFS
bind-mounts break SQLite advisory locks.

## Notes

- Default command is `--help`; pass any `pf-agent` args after the service name.
- `PF_AGENT_SKIP_FIRST_RUN=1` keeps `docker compose up` non-interactive.
- Override the service port with `PF_AGENT_SERVICE_PORT` (default 8765).
- Timezone defaults to UTC; set `TZ=Asia/Shanghai` in the environment to change.
- The image never bakes secrets: `.env` is excluded by `.dockerignore`.
