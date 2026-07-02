# Task 192: Docker And Compose Distribution / Docker 与 Compose 分发

## Goal

Ship a **production Dockerfile** and two **docker-compose** manifests
(`docker-compose.yml` and `docker-compose.windows.yml`) so users who don't
want to touch Python can run ProseForge Agent with:

```bash
docker compose up
```

The image is small, contains only the runtime dependencies, respects the
Task 190 bootstrap (UTF-8, path hardening), mounts a persistent workspace
at `/data`, and exposes the local agent service API port (Task 55).

## Agent Product Requirement

A meaningful fraction of new users want a container: no Python, no venv,
no PATH surgery. Hermes ships both a Linux compose and a Windows compose
(Windows Docker Desktop needs bind-mount adjustments). This card matches
that surface.

## Architecture Notes

Image strategy:

- **Base**: `python:3.11-slim-bookworm`.
- **User**: dedicated non-root `pfagent` (uid 1000) to avoid file-ownership
  headaches on bind-mounts.
- **Install path**: `pip install proseforge-agent==<version>` (from PyPI
  after Task 189) or `pip install /src` (Docker build ARG `PF_AGENT_SOURCE=local`).
- **Entrypoint**: a thin shell script that runs
  `python -m proseforge_agent._bootstrap`, then `exec pf-agent "$@"`.
- **Workspace mount**: `/data` (host path is user-selectable in compose).
- **Config mount**: `/config` (read-only for `.env`, providers YAML).
- **Ports**: expose the local agent service (Task 55) on `8765` by default,
  configurable via `PF_AGENT_SERVICE_PORT`.

The `docker-compose.windows.yml` variant differs only in:

- Uses a **named volume** for `/data` (Windows bind-mount fs semantics
  break sqlite locking).
- Sets `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8` explicitly.
- Adds `tty: true` and `stdin_open: true` for chat REPL usability.

We also add a `dockerignore` to prevent copying `.git`, `.venv`, `.pytest_cache`,
`node_modules`, and every fixture directory into the image (large + private).

Read before starting:

- 55-local-agent-service-api.md
- 190-windows-utf8-early-bootstrap.md
- 191-dotenv-support-and-example.md
- 00-task-index.md

## Files

- Create `Dockerfile` at repo root.
- Create `.dockerignore` at repo root.
- Create `docker-compose.yml`.
- Create `docker-compose.windows.yml`.
- Create `docker/entrypoint.sh`.
- Create `docker/README.md` (short quick-start; not the marketing README).
- Add tests in `tests/test_docker_distribution.py` (planner-style; do not
  actually build the image in CI unless a `PF_AGENT_BUILD_DOCKER=1` env
  flag is present).
- Add fixtures under `tests/fixtures/docker-and-compose-distribution/`:
  `sample_compose.yml`, `sample_windows_compose.yml`.

## Interfaces / Contracts

- `install.docker_plan.DockerImagePlan.from_repo(root: Path).steps()` — a
  deterministic list of `("layer_name", "command")` pairs mirroring the
  Dockerfile line-by-line so we can assert order in tests.
- Compose files must declare:
  - service `pf-agent` with `build: .` and `image: proseforge-agent:latest`.
  - volumes `pf-agent-data:/data` (or bind on Linux compose).
  - environment `PF_AGENT_WORKSPACE=/data`, `PROSEFORGE_ROOT=/opt/proseforge`.
  - ports `${PF_AGENT_SERVICE_PORT:-8765}:8765`.
- Entrypoint script contract:
  - `docker run image` (no args) → `pf-agent` (bare, which will REPL per
    Task 186).
  - `docker run image chat --message hi` → `pf-agent chat --message hi`.

## Data Flow

1. `docker build .` → applies the Dockerfile: system deps → `pip install`
   → copy entrypoint → set user to `pfagent`.
2. `docker compose up` → mounts `/data` + `/config`, exposes port,
   `docker run` semantics dispatch args.
3. Entrypoint runs bootstrap, then execs pf-agent.
4. On `docker compose exec pf-agent pf-agent chat`, container serves the
   REPL over the attached PTY.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_docker_distribution.py::test_dockerfile_uses_python_311_slim_and_non_root_user`**

```python
def test_dockerfile_uses_python_311_slim_and_non_root_user(repo_root):
    dockerfile = (repo_root / "Dockerfile").read_text(encoding="utf-8")
    assert "python:3.11-slim" in dockerfile
    assert "USER pfagent" in dockerfile
    assert "ENTRYPOINT" in dockerfile
```

- [ ] **Step 2: Run the targeted test and confirm failure.**

- [ ] **Step 3: Write the Dockerfile, entrypoint, compose files, and the
  planner.**

- [ ] **Step 4: Run the targeted test and confirm pass.**

- [ ] **Step 5: Add companion tests**

```text
test_dockerignore_excludes_git_venv_and_pytest_cache
test_compose_linux_binds_workspace_volume
test_compose_windows_uses_named_volume_for_workspace
test_entrypoint_script_passes_all_args_through_to_pf_agent
test_docker_image_plan_steps_match_dockerfile_lines
test_compose_files_declare_service_port_from_env
test_windows_compose_sets_pythonutf8_env_var
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_docker_distribution.py -q
docker build -t proseforge-agent:dev .
docker run --rm proseforge-agent:dev --help
docker compose -f docker-compose.yml config
docker compose -f docker-compose.windows.yml config
```

- [ ] **Step 7: Run full repository verification**

```powershell
python -m pytest -q
```

- [ ] **Step 8: Record commit boundary**

```powershell
git add Dockerfile .dockerignore docker-compose.yml docker-compose.windows.yml docker/ src/proseforge_agent/install/docker_plan.py tests/test_docker_distribution.py tests/fixtures/docker-and-compose-distribution
git commit -m "feat: add docker and compose distribution"
```

## Cross-Platform Notes

- Linux compose uses bind-mount `./data:/data` — same UID mapping as the
  `pfagent` user.
- Windows compose uses a **named volume** for `/data` — bind-mounts to
  NTFS break SQLite advisory locks.
- Both compose files declare `command: ["--help"]` as default so
  `docker compose up` on a fresh checkout is safe.
- Container timezone defaults to UTC; document how to override with
  `TZ=Asia/Shanghai`.

## Failure Modes To Prove

- Bind-mounting a `data` folder whose UID != 1000 does not crash — the
  entrypoint chmods the dir if owned by root inside the container.
- Missing `.env` at `/config` is silent; missing providers YAML degrades to
  the fake provider with a warning.
- The image respects `PF_AGENT_SKIP_FIRST_RUN=1` so `docker run` in CI is
  non-interactive.
- The image never contains secrets — the build refuses if `.env` is
  present at build time (via `.dockerignore` + a build-time check).

## Verification

```powershell
python -m pytest tests/test_docker_distribution.py -q
docker compose -f docker-compose.yml config
python -m pytest -q
```

## Acceptance

- `docker build .` produces an image under 300 MB.
- `docker compose up` on a fresh machine, with a placeholder `.env`, boots
  the container and answers `docker compose exec pf-agent pf-agent --version`.
- Windows Docker Desktop users can point their Compose UI at
  `docker-compose.windows.yml` and get the same result.

## Commit Boundary

Commit only the Dockerfile, dockerignore, compose files, entrypoint, the
planner, tests, and fixtures. Do not bundle install scripts (Task 187),
first-run auto-trigger (Task 188), or documentation (193/194).
