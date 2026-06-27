# Task 35: Chat CLI REPL

## Goal

Add `pf-agent chat` as an interactive terminal chat surface plus a one-shot message mode.

## Agent Product Requirement

Users must be able to talk to the agent directly. The product cannot be only command-driven novel automation.

## Architecture Notes

The REPL uses Agent Kernel. It does not call providers, memory, retrieval, workflow, or tools directly.

## Files

- Create `src/proseforge_agent/chat/repl.py`
- Modify `src/proseforge_agent/cli.py`
- Create `tests/test_chat_cli_repl.py`
- Create `tests/fixtures/chat/repl_inputs.txt`

## Interfaces / Contracts

- `pf-agent chat` starts interactive mode.
- `pf-agent chat --message <text>` runs one turn and exits.
- `--project <slug>` binds project chat.
- `--mode <mode>` selects conversation mode.
- `--permission-level <level>` sets the maximum permission.
- Slash commands: `/exit`, `/mode`, `/project`, `/sessions`, `/help`.

## Data Flow

1. Parse chat CLI flags.
2. Load config and chat session store.
3. Create or resume session.
4. For each user input, call `AgentKernel.run_turn()`.
5. Print response.
6. Save transcript and events.
7. Exit cleanly on `/exit` or EOF.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_chat_cli_repl.py::test_chat_message_mode_prints_fake_response`**

```python
def test_chat_message_mode_prints_fake_response(cli_runner, fake_kernel):
    result = cli_runner.invoke(["chat", "--message", "hello", "--provider", "fake"])
    assert result.exit_code == 0
    assert result.output.strip()
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/test_chat_cli_repl.py::test_chat_message_mode_prints_fake_response -q
```

Expected: FAIL because the `chat` command and REPL are missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement chat subcommand, one-shot message mode, kernel call, response printing, exit code handling, and session creation.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/test_chat_cli_repl.py::test_chat_message_mode_prints_fake_response -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

Required tests:

```text
test_chat_repl_exit_command_returns_zero
test_chat_project_flag_sets_project_chat_mode
test_chat_permission_level_defaults_to_read_only
test_chat_resume_loads_existing_session
test_chat_help_lists_slash_commands
test_chat_eof_exits_without_stack_trace
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_chat_cli_repl.py -q
pf-agent chat --message "hello" --provider fake
```

Expected: command exits 0, prints a response, and writes a session transcript.

## Cross-Platform Notes

- REPL uses standard input and output only.
- PowerShell, Bash, Zsh, and Fish use the same command shape.
- UTF-8 input and output are required.
- EOF behavior must work in non-interactive shells.

## Failure Modes To Prove

- EOF exits 0 without stack trace.
- Missing project slug in project mode prints recovery command.
- Kernel error prints trace id and support bundle hint.
- Unsupported mode fails before starting a session.

## Verification

```powershell
python -m pytest tests/test_chat_cli_repl.py -q
pf-agent chat --message "hello" --provider fake
```

## Acceptance

- `pf-agent chat --message` works in non-interactive shells.
- `pf-agent chat` works interactively.
- Chat output is saved to a session.
- The command works without a novel project.
- Project chat binds to project slug when requested.

## Commit Boundary

Commit chat CLI files and tests only after verification passes.
