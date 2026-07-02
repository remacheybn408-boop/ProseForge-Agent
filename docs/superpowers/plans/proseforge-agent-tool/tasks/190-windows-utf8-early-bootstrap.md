# Task 190: Windows UTF-8 Early Bootstrap / Windows UTF-8 早期引导

## Goal

Add an **early bootstrap module** that fixes Windows text encoding issues
before any user code runs. Ensure the CLI, chat REPL, tool output, and log
files can round-trip CJK, emoji, and non-ASCII paths on Windows PowerShell
and legacy `cmd.exe` without `UnicodeEncodeError`.

## Agent Product Requirement

Chinese-speaking users are a primary audience. On Windows, `print("你好")` in
the default `cp936` console still raises `UnicodeEncodeError` in many
setups. Every "just works" agent CLI (Codex, Claude Code, Hermes) ships
this fix as its first line of code. Without it, our own core users are
locked out of features that work fine on macOS/Linux.

## Architecture Notes

Hermes handles this in `hermes_bootstrap.py`. We mirror that with
`src/proseforge_agent/_bootstrap.py`, imported at the very top of every
process entry point (`cli.py`, `chat/repl.py`, `demo.py`,
`__main__.py` for `python -m proseforge_agent`).

The bootstrap does four things — no more, no less — and is safe to import
multiple times (idempotent, guarded by `if getattr(sys, "_pf_agent_bootstrapped", False)`):

1. **Force UTF-8 for child processes**: set `PYTHONUTF8=1` and
   `PYTHONIOENCODING=utf-8` in `os.environ` if not already set.
2. **Reconfigure I/O streams** to UTF-8 with `errors="replace"`. On
   `TextIOWrapper` streams call `.reconfigure(encoding="utf-8", errors="replace")`.
3. **Harden `sys.path`**: put the package's source root at index 0; strip
   the current working directory to prevent third-party `utils.py` /
   `agent.py` from shadowing our modules.
4. **Activate a writable lazy-install directory** on read-only container
   deploys (Docker images with an unwritable `/app`): add a per-user
   writable dir to `sys.path` if it exists.

We do NOT patch `locale.getpreferredencoding` because that has been
observed to break some Windows `subprocess` flows.

Read before starting:

- 44-cross-platform-app-directories.md
- 45-native-secret-storage.md
- 186-default-chat-repl-on-bare-command.md
- 00-task-index.md

## Files

- Create `src/proseforge_agent/_bootstrap.py`.
- Modify `src/proseforge_agent/cli.py` — add `import proseforge_agent._bootstrap  # noqa: F401` as the FIRST import (above `from __future__ import annotations`).
- Modify `src/proseforge_agent/chat/repl.py` — same top-of-file import.
- Modify `src/proseforge_agent/demo.py` — same top-of-file import.
- Create `src/proseforge_agent/__main__.py` — same top-of-file import, then delegates to `cli.main`.
- Add tests in `tests/test_windows_utf8_bootstrap.py`.
- Add fixtures under `tests/fixtures/windows-utf8-bootstrap/`:
  `unicode_input_samples.json` (contains 中文, emoji, RTL, combining marks).

## Interfaces / Contracts

- `proseforge_agent._bootstrap.install()` — idempotent bootstrap invocation.
  Automatically called on import.
- `proseforge_agent._bootstrap.STATE` — dict with keys
  `already_installed`, `python_utf8_set`, `stdout_reconfigured`,
  `stderr_reconfigured`, `stdin_reconfigured`, `sys_path_hardened`.
- The bootstrap must NEVER raise. Every op is wrapped in try/except and any
  failure is recorded in a `warnings` field on `STATE`.

## Data Flow

1. Any entry point starts.
2. First import is `proseforge_agent._bootstrap`.
3. Bootstrap sets env vars, reconfigures streams, hardens path.
4. Rest of module imports proceed against a UTF-8-safe interpreter.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_windows_utf8_bootstrap.py::test_bootstrap_sets_python_utf8_and_reconfigures_streams`**

```python
def test_bootstrap_sets_python_utf8_and_reconfigures_streams(monkeypatch):
    monkeypatch.delenv("PYTHONUTF8", raising=False)
    monkeypatch.delenv("PYTHONIOENCODING", raising=False)
    monkeypatch.setattr(sys, "_pf_agent_bootstrapped", False, raising=False)

    import importlib
    from proseforge_agent import _bootstrap
    importlib.reload(_bootstrap)

    assert os.environ["PYTHONUTF8"] == "1"
    assert os.environ["PYTHONIOENCODING"].lower().startswith("utf-8")
    assert _bootstrap.STATE["stdout_reconfigured"] in (True, "not_a_text_wrapper")
```

- [ ] **Step 2: Run the targeted test and confirm failure.**

- [ ] **Step 3: Implement `_bootstrap.py` and wire the imports.**

- [ ] **Step 4: Run the targeted test and confirm pass.**

- [ ] **Step 5: Add companion tests**

```text
test_bootstrap_is_idempotent
test_bootstrap_hardens_syspath_and_removes_cwd
test_bootstrap_never_raises_on_missing_streams
test_bootstrap_activates_lazy_install_dir_when_present
test_repl_prints_cjk_and_emoji_without_error_on_utf8_stream
test_cli_help_output_contains_no_replacement_char_when_terminal_is_utf8
```

- [ ] **Step 6: Run subsystem verification**

```powershell
$env:PYTHONUTF8 = ""
python -m proseforge_agent.cli --help | Out-String -Width 200
python -m proseforge_agent.chat.repl <<< "你好，世界 🚀"
```

- [ ] **Step 7: Run full repository verification**

```powershell
python -m pytest -q
```

- [ ] **Step 8: Record commit boundary**

```powershell
git add src/proseforge_agent/_bootstrap.py src/proseforge_agent/__main__.py src/proseforge_agent/cli.py src/proseforge_agent/chat/repl.py src/proseforge_agent/demo.py tests/test_windows_utf8_bootstrap.py tests/fixtures/windows-utf8-bootstrap
git commit -m "feat: add windows utf-8 early bootstrap"
```

## Cross-Platform Notes

- On macOS/Linux the bootstrap is a no-op (env already UTF-8) but must
  still record `STATE` for observability.
- On `python -c "..."` invocations where `sys.stdout` is not a
  `TextIOWrapper`, silently skip stream reconfiguration; do not raise.
- On Termux and Alpine (musl), `.reconfigure()` should behave normally
  but the `sys.path` hardening must respect `PYTHONPATH` if set.

## Failure Modes To Prove

- A missing `sys.stdout.reconfigure` (older embedded Python) does not
  raise.
- The bootstrap is safe to import twice.
- Deleting the source root from `sys.path` after import does not break
  subsequent imports.
- A malformed `PYTHONPATH` is preserved verbatim (we only prepend).

## Verification

```powershell
python -m pytest tests/test_windows_utf8_bootstrap.py -q
python -m pytest -q
```

## Acceptance

- On a raw Windows 10/11 `cmd.exe`, `pf-agent --help` prints CJK segments
  from `--help` and `--description` fields with no `UnicodeEncodeError`.
- On macOS/Linux, the bootstrap is a no-op with `STATE["already_installed"]`
  or `STATE["python_utf8_set"] == "preexisting"`.
- 1035+ existing tests still pass; +6 new tests.

## Commit Boundary

Commit only the bootstrap module, the entry-point imports, tests, and
fixtures. Do not bundle the default REPL router (186), auto-trigger
(188), or .env support (191).
