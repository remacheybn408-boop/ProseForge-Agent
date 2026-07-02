# Task 195: CLI Config YAML Example Seed / CLI 配置样板

## Goal

Ship a single, fully-commented, ready-to-copy YAML file — `configs/pf-agent.example.yaml` —
that documents every configuration knob a user can set for `pf-agent`, and a
`pf-agent init --config` command that copies it to the resolved config path
with placeholders filled in from the current environment.

## Agent Product Requirement

Reading source is a barrier to entry. Users want a **single starting file**
they can copy, edit, and run. Hermes ships `cli-config.yaml.example`; every
polished CLI does the same. Without this, a new user has to piece together
config keys from docs, provider profiles, and code.

## Architecture Notes

We already have piecemeal examples: `configs/providers.example.yaml`, per-provider
YAML under `configs/providers/`, a `configs/agent.example.yaml` (if not
present, this card creates it). What we lack is one **master example** that
composes them and covers the top-of-stack knobs added between tasks 100–185
(observability, middleware, skills, cron, telemetry, MCP).

Design:

- The example file lives at `configs/pf-agent.example.yaml`.
- Every knob is grouped by concern (workspace, providers, retrieval, memory,
  chat, telemetry, cron, mcp, gateway, execution, skills, safety).
- Every knob has a comment above it: what it does, the default, and a
  pointer to the task card that owns it.
- `pf-agent init --config [--path PATH]` copies the example to the resolved
  config path (default `<AppDirs.config_dir>/pf-agent.yaml`), refuses to
  overwrite unless `--force` is set, and substitutes `${VAR}` placeholders
  from the current env.

A test-golden pass extracts every known config key from the code (using a
lightweight AST scan of `config_generator.py` and provider registries) and
asserts the example file mentions each. This prevents future features from
silently drifting past the example.

Read before starting:

- 02-config-and-workspace.md
- 78-setup-config-generator.md
- 191-dotenv-support-and-example.md
- 00-task-index.md

## Files

- Create `configs/pf-agent.example.yaml` — the master example.
- Modify `src/proseforge_agent/setup/config_generator.py` to expose a
  `known_config_keys() -> set[str]` helper that returns every config key the
  generator can write.
- Modify `src/proseforge_agent/cli.py` — extend the existing `init` command
  group with a `--config` mode that copies the example to the resolved path.
- Add tests in `tests/test_cli_config_yaml_example_seed.py`.
- Add fixtures under `tests/fixtures/cli-config-yaml-example-seed/`:
  `expected_keys.json`, `substituted_sample.yaml`.

## Interfaces / Contracts

- `configs/pf-agent.example.yaml` — top-level YAML with these sections:
  `workspace`, `providers`, `retrieval`, `memory`, `chat`, `telemetry`,
  `cron`, `mcp`, `gateway`, `execution`, `skills`, `safety`. Every leaf
  key has a one-line `# comment` above it.
- CLI: `pf-agent init --config [--path PATH] [--force]` — copies the
  example, substitutes `${VAR}` from `os.environ`, refuses to overwrite
  existing files.
- `setup.config_generator.known_config_keys() -> set[str]` — a stable,
  test-facing surface.
- Golden test: every string in `known_config_keys()` must appear in
  `configs/pf-agent.example.yaml`.

## Data Flow

1. User runs `pf-agent init --config`.
2. CLI resolves target path via `AppDirs.config_dir / "pf-agent.yaml"`.
3. If target exists and no `--force`, exits 3 with "target exists" message.
4. Reads `configs/pf-agent.example.yaml` as UTF-8, applies `${VAR}`
   substitution.
5. Writes atomically (tmp file + rename) with mode 600 on POSIX.
6. Prints the resolved path and a "next: `pf-agent`" line.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_cli_config_yaml_example_seed.py::test_example_yaml_contains_every_known_config_key`**

```python
def test_example_yaml_contains_every_known_config_key(repo_root):
    text = (repo_root / "configs/pf-agent.example.yaml").read_text(encoding="utf-8")
    for key in known_config_keys():
        assert key in text, f"example missing key: {key}"
```

- [ ] **Step 2: Run the targeted test and confirm failure.**

- [ ] **Step 3: Author the example YAML, implement `known_config_keys()`,
  extend `init --config`.**

- [ ] **Step 4: Run the targeted test and confirm pass.**

- [ ] **Step 5: Add companion tests**

```text
test_init_config_copies_example_to_resolved_path
test_init_config_refuses_to_overwrite_without_force
test_init_config_substitutes_env_var_placeholders
test_init_config_writes_atomic_and_600_permissions_on_posix
test_example_yaml_is_valid_yaml
test_example_yaml_every_section_has_at_least_one_key
test_every_task_card_owning_a_config_knob_is_referenced_by_comment
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_cli_config_yaml_example_seed.py -q
pf-agent init --config --path $env:TEMP\pf-agent.yaml
Get-Content $env:TEMP\pf-agent.yaml | Select-Object -First 40
```

- [ ] **Step 7: Run full repository verification**

```powershell
python -m pytest -q
```

- [ ] **Step 8: Record commit boundary**

```powershell
git add configs/pf-agent.example.yaml src/proseforge_agent/setup/config_generator.py src/proseforge_agent/cli.py tests/test_cli_config_yaml_example_seed.py tests/fixtures/cli-config-yaml-example-seed
git commit -m "feat: add cli config yaml example seed"
```

## Cross-Platform Notes

- POSIX: written with mode 600 (owner read/write only).
- Windows: `os.chmod` with 600 is a no-op; document that the file is
  under `%APPDATA%` which is per-user.
- Line endings: LF in the checked-in example; the writer preserves LF on
  all platforms (do not convert to CRLF on Windows).
- Encoding: UTF-8, no BOM.

## Failure Modes To Prove

- Copying to a target that already exists refuses with exit 3 and the
  exact message `"target exists; use --force to overwrite"`.
- A malformed `${VAR}` in the example is preserved verbatim (no
  half-substituted output) and reported as a warning.
- Missing env vars leave the placeholder intact; the user can fill it in
  manually and re-run.
- The example YAML is valid YAML (parse in test).
- Every section header from the design section appears in the example.

## Verification

```powershell
python -m pytest tests/test_cli_config_yaml_example_seed.py -q
python -m pytest -q
```

## Acceptance

- Users can run `pf-agent init --config` to get a working starting file
  in the correct per-user location.
- The example file grows organically with the project because the golden
  test blocks silent drift.
- The `--config` flag composes with `--path` and `--force` so scripts and
  humans both have a good path.

## Commit Boundary

Commit only the example YAML, the `known_config_keys()` helper, the CLI
extension, tests, and fixtures. Do not bundle installer scripts (187),
first-run auto-trigger (188), .env support (191), Docker (192), or
community docs (194).
