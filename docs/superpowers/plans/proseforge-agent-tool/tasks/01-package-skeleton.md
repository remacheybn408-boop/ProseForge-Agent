# Task 01: Package Skeleton

## Goal

Create the importable Python package, base errors, CLI shell, and project metadata.

## Architecture Notes

This task creates only the smallest package spine. Later tasks add behavior behind these public modules.

Read before starting:

- ../architecture/02-system-architecture.md
- ../appendices/01-data-contracts.md
- 00-task-index.md

## Files

- Create `pyproject.toml`
- Create `README.md`
- Create `src/proseforge_agent/__init__.py`
- Create `src/proseforge_agent/errors.py`
- Create `src/proseforge_agent/cli.py`
- Create `tests/test_package.py`
- Create `tests/test_cli.py`

## Interfaces / Contracts

`proseforge_agent.__version__` is `"0.1.0"`; `pf-agent --help` exits 0; all package exceptions inherit `ProseForgeAgentError`.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_package.py::test_package_exposes_version_and_errors`**

```python
from proseforge_agent import __version__
from proseforge_agent.errors import ConfigurationError, ProseForgeAgentError


def test_package_exposes_version_and_errors():
    assert __version__ == "0.1.0"
    assert issubclass(ConfigurationError, ProseForgeAgentError)
```

- [ ] **Step 2: Run the targeted test and confirm failure**

Run:

```powershell
python -m pytest tests/test_package.py::test_package_exposes_version_and_errors -q
```

Expected: FAIL with `ModuleNotFoundError: No module named proseforge_agent`.

- [ ] **Step 3: Implement the minimum production behavior**

Add package metadata, `__version__`, error classes, and a minimal `cli.main(argv=None)` that prints help through argparse.

- [ ] **Step 4: Run the targeted test and confirm pass**

Run:

```powershell
python -m pytest tests/test_package.py::test_package_exposes_version_and_errors -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Run integration verification**

Run:

```powershell
python -m pytest tests/test_package.py tests/test_cli.py -q
python -m proseforge_agent.cli --help
```

Expected: command exits 0 and writes only the artifacts named in this card.

- [ ] **Step 6: Record commit boundary**

```powershell
git add pyproject.toml tests
git commit -m "feat: add package skeleton"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Verification

```powershell
python -m pytest tests/test_package.py tests/test_cli.py -q
python -m proseforge_agent.cli --help
```

## Acceptance

- Package imports without reading config, filesystem state, or API keys.
- CLI help works before any project is initialized.
- No provider, memory, or workflow behavior is added here.

## Commit Boundary

Commit after this card passes verification. Do not start the next card with failing tests or unreviewed artifacts from this card.
