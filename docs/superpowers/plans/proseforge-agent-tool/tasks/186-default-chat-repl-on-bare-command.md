# Task 186: Default Chat REPL On Bare Command / 无参启动即进对话

## Goal

Change `pf-agent` (no arguments) from "print help" to "start an interactive
chat REPL" when the environment is already configured, and to "start the
provider setup wizard" when it is not. Ordinary users should be able to type
`pf-agent` and end up in a working conversation without knowing any subcommands.

## Agent Product Requirement

Hermes / Codex / Claude Code all follow the same shape: the tool's name is the
launcher. New users type it and the tool decides what to do next based on
whether their machine is already provisioned. Right now `pf-agent` prints a
help block, which is a dead-end for users who don't know the command tree.

## Architecture Notes

The change is a tiny router in `cli.main()`. Today at `src/proseforge_agent/cli.py:6177`
we have:

```python
if not getattr(args, "command", None):
    parser.print_help()
    return 0
```

We replace that branch with a **default-command router** that:

1. Detects whether a provider config resolves via existing loader
   `proseforge_agent.config.load_agent_config` (Task 02). Reuse
   `install.provider_setup.ProviderSetupWizard` (called at `cli.py:3164`) to
   decide "configured vs not".
2. If configured → invoke the existing chat REPL entry
   `proseforge_agent.chat.repl.main` (already used by
   `python -m proseforge_agent.chat.repl`).
3. If not configured → invoke `install.first_run.FirstRunWizard` (already
   imported at `cli.py:5273`) and, on success, tail-recurse into (2).
4. Preserve a hidden opt-out: `pf-agent --help` still prints help; a new
   `pf-agent --no-default` prints help and exits 0, so scripts that depend on
   the old bare-command behavior can be rescued with one flag.

We do NOT introduce a new subcommand. `pf-agent chat` continues to exist and
does the same thing; the change is only in how bare `pf-agent` dispatches.

Read before starting:

- ../architecture/08-agent-runtime-and-chat.md (Chat REPL entry)
- 38-chat-cli-repl.md
- 45-provider-setup-wizard.md
- 46-first-run-onboarding-wizard.md
- 00-task-index.md

## Files

- Modify `src/proseforge_agent/cli.py` (main() dispatch, add `--no-default`).
- Modify `src/proseforge_agent/chat/repl.py` (expose a `run_repl()` callable
  suitable for programmatic entry; keep `main()` for `python -m` invocation).
- Add tests in `tests/test_default_chat_repl_on_bare_command.py`.
- Add fixtures under `tests/fixtures/default-chat-repl-on-bare-command/` only
  when a deterministic empty-config workspace is needed.

## Interfaces / Contracts

- `pf-agent` (no args) → chat REPL when provider config resolves; else the
  first-run wizard.
- `pf-agent --no-default` → prints help and exits 0.
- `pf-agent --help` → unchanged.
- Programmatic entry: `proseforge_agent.chat.repl.run_repl(argv: list[str] | None = None, provider: str = "fake") -> int`.
- Router signature: internal `_dispatch_bare_command(args: argparse.Namespace) -> int`.

## Data Flow

1. `main(argv)` parses; when `args.command is None` and `args.no_default is
   False`, call `_dispatch_bare_command(args)`.
2. `_dispatch_bare_command` asks `ProviderSetupWizard().status()` (add if
   missing — see companion test) whether provider config is present and valid.
3. If ok → `chat.repl.run_repl(argv=[], provider=<resolved>)`.
4. If not → `FirstRunWizard().run(interactive=True)`; on success, retry (3).
5. Any exception during (3)/(4) is caught, formatted, and returned as exit 2
   with a one-line summary — never a Python traceback into the terminal.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_default_chat_repl_on_bare_command.py::test_bare_command_launches_chat_repl_when_provider_is_configured`**

```python
def test_bare_command_launches_chat_repl_when_provider_is_configured(monkeypatch, tmp_path):
    called = {}
    def fake_run_repl(argv=None, provider="fake"):
        called["provider"] = provider
        return 0
    monkeypatch.setattr("proseforge_agent.chat.repl.run_repl", fake_run_repl)
    monkeypatch.setattr(
        "proseforge_agent.install.provider_setup.ProviderSetupWizard.status",
        lambda self: {"configured": True, "provider": "fake"},
    )
    exit_code = main([])
    assert exit_code == 0
    assert called["provider"] == "fake"
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/test_default_chat_repl_on_bare_command.py::test_bare_command_launches_chat_repl_when_provider_is_configured -q
```

Expected: FAIL because bare `pf-agent` still calls `parser.print_help()`.

- [ ] **Step 3: Implement**

Replace the `not args.command` branch in `cli.main()` with `_dispatch_bare_command`.
Add the `--no-default` flag on the top-level parser. Add `chat.repl.run_repl`.
Add `ProviderSetupWizard.status()` (returning `{"configured": bool,
"provider": str|None, "reason": str}`) if it doesn't already exist.

- [ ] **Step 4: Run the targeted test and confirm pass**

- [ ] **Step 5: Add companion tests**

```text
test_bare_command_launches_first_run_when_not_configured
test_no_default_flag_prints_help_and_exits_zero
test_bare_command_never_prints_python_traceback_on_repl_error
test_help_flag_still_prints_help_before_dispatch
test_bare_command_returns_nonzero_when_first_run_declined
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_default_chat_repl_on_bare_command.py -q
python -m proseforge_agent.cli --help | Select-String -Pattern "no-default"
```

- [ ] **Step 7: Run full repository verification**

```powershell
python -m pytest -q
```

- [ ] **Step 8: Record commit boundary**

```powershell
git add src/proseforge_agent/cli.py src/proseforge_agent/chat/repl.py tests/test_default_chat_repl_on_bare_command.py
git commit -m "feat: default chat repl on bare command"
```

## Cross-Platform Notes

- The `--no-default` flag prevents shell scripts from accidentally entering an
  interactive REPL when `pf-agent` is called from a pipeline.
- On Windows PowerShell the REPL should honor whatever encoding the Task 190
  bootstrap installs; do not add encoding shims here.
- On macOS/Linux, `pf-agent < /dev/null` must still exit 0 with a "no input"
  message rather than blocking on stdin.

## Failure Modes To Prove

- A REPL runtime exception is caught and reported without a Python traceback.
- A user who declines the first-run wizard gets exit code 2, not a crash.
- `--no-default` restores legacy print-help behavior.
- `--help` short-circuits before dispatch.
- With a broken (unreadable) config file, the router falls through to the
  first-run wizard with a clear reason line.

## Verification

```powershell
python -m pytest tests/test_default_chat_repl_on_bare_command.py -q
pf-agent                # in an already-configured workspace → chat REPL
pf-agent --no-default   # prints help
python -m pytest -q
```

## Acceptance

- `pf-agent` with no args launches the chat REPL when configured, else the
  first-run wizard.
- `pf-agent --help` and `pf-agent --no-default` preserve the pre-186 behavior.
- No Python traceback ever reaches the terminal from the default router.
- All 1035+ existing tests continue to pass; +5 new tests.

## Commit Boundary

Commit only the cli/repl router change and its tests. Do not bundle the
managed install script (Task 187) or first-run auto-trigger polish
(Task 188) into this commit.
