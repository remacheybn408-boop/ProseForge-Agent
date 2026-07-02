# Release Runbook — PyPI Publish (Task 189)

The publish runner is exercised in tests with an injectable runner; the
**actual publish** is an out-of-band action performed by a maintainer or CI
with real credentials. Never commit a token.

## 1. Bump the version

```powershell
pf-agent release bump --kind patch          # prints: current 0.1.0 -> next 0.1.1
pf-agent release bump --kind patch --write   # also rewrites pyproject.toml
```

```bash
pf-agent release bump --kind minor --write
```

Kinds: `patch` / `minor` / `major` / `prerelease` (`--pre-id rc`).

Commit the version bump before publishing.

## 2. Publish to TestPyPI first

PowerShell:

```powershell
$env:TWINE_USERNAME = "__token__"
$env:TWINE_PASSWORD = "<testpypi-token>"
pf-agent release publish --repository testpypi
python -m pip install --index-url https://test.pypi.org/simple/ proseforge-agent
pf-agent --version
```

Bash:

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=<testpypi-token>
pf-agent release publish --repository testpypi
```

Use `--dry-run` first to print the plan without uploading.

## 3. Publish to PyPI

```powershell
$env:TWINE_PASSWORD = "<pypi-token>"
pf-agent release publish --repository pypi
```

## Guarantees

- `release publish` refuses a version already present on the target index
  (duplicate check via the PyPI JSON API, fail-open on fetch error).
- Credentials are read from `TWINE_USERNAME` / `TWINE_PASSWORD` and passed to
  the child process env only — never embedded in argv, the report, or logs.
- The Task 47 `PackageChecker` gate runs before any upload.
