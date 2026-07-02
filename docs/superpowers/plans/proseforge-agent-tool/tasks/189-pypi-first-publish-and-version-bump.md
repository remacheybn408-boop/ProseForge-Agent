# Task 189: PyPI First Publish And Version Bump Discipline / 首次发布 PyPI + 版本纪律

## Goal

Execute the first real publish of `proseforge-agent` to **TestPyPI** and then
to **PyPI**, using the Task 183 `PyPIPublisher`. Add a lightweight
**version-bump discipline** so subsequent publishes cannot accidentally
duplicate a version already on the target index.

## Agent Product Requirement

Task 183 built the runner but never ran it. Until we perform the first
publish, the one-line install script (Task 187) has nothing to install. This
card takes the runner from "verified in tests" to "verified on the wire" and
establishes the pattern for every subsequent release.

## Architecture Notes

Two moving parts:

1. **Publish execution** — a documented, checked-in runbook driven by a new
   `pf-agent release publish` CLI command that wraps
   `release.publish.PyPIPublisher`. The command reads credentials from env
   (`TWINE_USERNAME` / `TWINE_PASSWORD`) or the native secret store (Task 45)
   under a keyed alias `pf-agent:pypi:<repository>`.
2. **Version-bump discipline** — a new
   `release.version_policy.VersionPolicy` that owns the version bump rules:
   `patch` / `minor` / `major` / `prerelease` selectors, refuses to publish
   the current committed version if it already exists on the target repo
   (using the same `published_versions_lookup` seam the publisher exposes),
   and can write the bumped version back to `pyproject.toml` behind an
   explicit `--write` flag.

The published-versions lookup uses the JSON API at
`https://pypi.org/pypi/<name>/json` (or the TestPyPI equivalent) via
`llm.http.UrllibTransport` so we reuse an already-tested transport rather
than adding requests/urllib3. A network-off test uses a fake transport that
returns pre-canned JSON.

Read before starting:

- 47-pip-pipx-source-installation.md
- 183-pypi-publish.md
- 00-task-index.md

## Files

- Create `src/proseforge_agent/release/version_policy.py`.
- Modify `src/proseforge_agent/cli.py` — extend the existing `release`
  command group with subcommands `bump` and `publish`.
- Modify `src/proseforge_agent/release/publish.py` — accept a
  `published_versions_lookup` implementation that hits PyPI JSON via
  `HttpTransport` (already exists at `llm/http.py`).
- Add tests in `tests/test_pypi_first_publish_and_version_bump.py`.
- Add fixtures under `tests/fixtures/pypi-first-publish-and-version-bump/`:
  `testpypi_index.json`, `pypi_index.json`.
- Add `docs/operators/release-runbook.md` describing the exact commands.

## Interfaces / Contracts

- `VersionPolicy(current: str).next(bump: Literal["patch","minor","major","prerelease"], pre_id: str = "rc") -> str`.
- `VersionPolicy.refuse_duplicate(candidate: str, published: set[str]) -> None` — raises `ConfigurationError` if candidate is in published.
- CLI:
  - `pf-agent release bump --kind patch [--pre-id rc] [--write]` → prints
    `current: 0.1.0 -> next: 0.1.1` and, with `--write`, updates
    `pyproject.toml`.
  - `pf-agent release publish --repository testpypi [--dry-run]` → wraps
    `PyPIPublisher`, reads credentials from env or secret store.
- HTTP-backed `PyPIPublishedVersions.for_repository(repository: str) -> set[str]`.

## Data Flow

1. `release bump` reads `[project].version` from `pyproject.toml`, computes
   the next version via `VersionPolicy`, and optionally writes it back.
2. `release publish --repository testpypi`:
   1. Calls `PackageChecker().verify()` (Task 47).
   2. Fetches published versions via `PyPIPublishedVersions`.
   3. Calls `VersionPolicy.refuse_duplicate`.
   4. Calls `PyPIPublisher.publish(repository, credentials=…)`.
3. On success, prints `Published <name>==<version> to <repository>` and the
   direct index URL (`https://test.pypi.org/project/<name>/<version>/`).

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_pypi_first_publish_and_version_bump.py::test_version_policy_bumps_patch_correctly`**

```python
def test_version_policy_bumps_patch_correctly():
    assert VersionPolicy("0.1.0").next("patch") == "0.1.1"
    assert VersionPolicy("0.1.0").next("minor") == "0.2.0"
    assert VersionPolicy("0.1.0").next("major") == "1.0.0"
    assert VersionPolicy("0.1.0").next("prerelease", pre_id="rc") == "0.1.1rc1"
```

- [ ] **Step 2: Run the targeted test and confirm failure.**

- [ ] **Step 3: Implement `VersionPolicy`, `PyPIPublishedVersions`, and CLI
  subcommands.**

- [ ] **Step 4: Run the targeted test and confirm pass.**

- [ ] **Step 5: Add companion tests**

```text
test_version_policy_refuses_duplicate
test_publish_lookup_parses_testpypi_index_json_fixture
test_publish_refused_when_current_version_already_published_on_target
test_release_publish_cli_uses_env_credentials
test_release_publish_cli_dry_run_never_calls_runner
test_release_bump_write_updates_pyproject_and_creates_commit_ready_diff
test_bump_and_publish_workflow_end_to_end_offline
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_pypi_first_publish_and_version_bump.py -q
pf-agent release bump --kind patch          # prints 0.1.0 -> 0.1.1
pf-agent release publish --repository testpypi --dry-run
```

- [ ] **Step 7: Run full repository verification**

```powershell
python -m pytest -q
```

- [ ] **Step 8: Perform the real first publish (out-of-band)**

Follow `docs/operators/release-runbook.md`:

```powershell
$env:TWINE_USERNAME = "__token__"
$env:TWINE_PASSWORD = "<testpypi-token>"
pf-agent release publish --repository testpypi
python -m pip install --index-url https://test.pypi.org/simple/ proseforge-agent
pf-agent --version   # → 0.1.1
$env:TWINE_PASSWORD = "<pypi-token>"
pf-agent release publish --repository pypi
```

- [ ] **Step 9: Record commit boundary (code only, real publish is out-of-band)**

```powershell
git add src/proseforge_agent/release/version_policy.py src/proseforge_agent/release/publish.py src/proseforge_agent/cli.py tests/test_pypi_first_publish_and_version_bump.py tests/fixtures/pypi-first-publish-and-version-bump docs/operators/release-runbook.md
git commit -m "feat: add version policy and release publish cli"
```

## Cross-Platform Notes

- Do not rely on `%APPDATA%` / `~/.local/share` for credential storage
  during the publish — read from env first; only fall back to the Task 45
  native secret storage.
- The runbook must include Windows PowerShell **and** Bash forms of the
  publish commands.
- `pyproject.toml` writes use a UTF-8 write that preserves the original
  newline style.

## Failure Modes To Prove

- Publishing a version already on the target index fails before build.
- Publishing without credentials fails at credential-load, not at upload
  (fail early with a clear "set TWINE_PASSWORD" message).
- A malformed version (`0.1`) raises `ConfigurationError` at bump time.
- The runbook publish step never prints the token, even under `--verbose`.

## Verification

```powershell
python -m pytest tests/test_pypi_first_publish_and_version_bump.py -q
python -m pytest -q
```

## Acceptance

- `VersionPolicy` computes the next version deterministically for
  patch/minor/major/prerelease.
- `pf-agent release publish` refuses duplicate versions.
- The runbook results in a working `pip install proseforge-agent` from
  PyPI. The version installed is the one committed in `pyproject.toml`.

## Commit Boundary

Commit only the version policy, the publish CLI wiring, tests, fixtures,
and the operator runbook. The **actual publish** is a runbook-driven,
out-of-band action performed by a human/CI with real credentials.
