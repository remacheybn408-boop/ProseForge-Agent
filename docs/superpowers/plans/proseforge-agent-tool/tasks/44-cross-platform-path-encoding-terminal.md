# Task 44: Cross-Platform Path Encoding And Terminal

## Goal

Guarantee path handling, UTF-8 text, shell quoting, and terminal output across Windows, macOS, and Linux.

## Agent Product Requirement

Novel projects often use Chinese filenames and paths with spaces; native support must treat that as normal.

## Architecture Notes

`platform_io` provides the shared primitives every other module uses for paths and terminal output: a shell command renderer that quotes correctly per shell, a UTF-8 safe writer/reader, and terminal capability detection (UTF-8 vs ASCII fallback). It is dependency-free at the bottom of the install stack; app dirs (43), doctor (42), shell integration (52), and CLI surfaces use it. It performs no provider or network calls.

Read before starting:

- ../architecture/02-system-architecture.md
- ../architecture/09-installation-and-native-platforms.md (Native Terminal Support)
- 00-task-index.md

## Files

- Create `src/proseforge_agent/install/platform_io.py`
- Create `tests/test_platform_io.py`
- Create `tests/fixtures/cross-platform-path-encoding-terminal/paths.json`

## Interfaces / Contracts

- `ShellCommandRenderer(shell: str).render(argv: list[str]) -> str` quotes arguments per shell (`powershell`, `cmd`, `bash`, `zsh`, `fish`).
- `TerminalCaps.detect(env) -> TerminalCaps` exposes `supports_utf8` and `ascii_fallback`.
- `write_text_utf8(path, text)` / `read_text_utf8(path)` always use UTF-8 and never corrupt Chinese characters.
- Paths containing spaces are always quoted; arguments are never concatenated unquoted.

## Data Flow

1. Detect the active shell and terminal encoding from the environment.
2. Render commands by quoting each argument for that shell.
3. Choose UTF-8 or ASCII-fallback rendering for terminal output.
4. Read/write text strictly as UTF-8.
5. Return rendered strings or capability flags to callers.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_platform_io.py::test_powershell_renderer_quotes_paths_with_spaces`**

```python
def test_powershell_renderer_quotes_paths_with_spaces():
    rendered = ShellCommandRenderer(shell="powershell").render(
        ["pf-agent", "doctor", "--config", "My Project/config.yaml"]
    )
    assert '"My Project/config.yaml"' in rendered or "'My Project/config.yaml'" in rendered
    assert "My Project/config.yaml" not in rendered.replace('"My Project/config.yaml"', "")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/test_platform_io.py::test_powershell_renderer_quotes_paths_with_spaces -q
```

Expected: FAIL because `ShellCommandRenderer` is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement `ShellCommandRenderer`, `TerminalCaps`, and the UTF-8 read/write helpers.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/test_platform_io.py::test_powershell_renderer_quotes_paths_with_spaces -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

```text
test_bash_renderer_quotes_paths_with_spaces
test_cmd_falls_back_to_ascii_when_terminal_lacks_utf8
test_write_then_read_round_trips_chinese_filename_content
test_terminal_caps_detect_reports_utf8_for_windows_terminal
test_argv_with_special_chars_is_never_left_unquoted
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_platform_io.py -q
pf-agent doctor --section encoding
```

Expected: tests pass and the `encoding` doctor section reports terminal UTF-8 capability.

- [ ] **Step 7: Run cross-platform contract check**

```powershell
python -m pytest tests/test_platform_io.py -q
```

Expected: PASS for the simulated PowerShell, CMD, Bash, Zsh, and Fish cases in the test file.

- [ ] **Step 8: Record commit boundary**

```powershell
git add src/proseforge_agent/install/platform_io.py tests/test_platform_io.py tests/fixtures/cross-platform-path-encoding-terminal
git commit -m "feat: add platform io"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Cross-Platform Notes

- Quoting rules cover PowerShell, CMD, Bash, Zsh, and Fish.
- UTF-8 is the default for all reads and writes.
- ASCII fallback is used only when the terminal cannot render UTF-8.

## Failure Modes To Prove

- A path with spaces is never emitted unquoted.
- Reading a Chinese filename's content round-trips without corruption.
- CMD without UTF-8 receives an ASCII fallback, not mojibake.
- Unknown shell name raises `ConfigurationError`.

## Verification

```powershell
python -m pytest tests/test_platform_io.py -q
pf-agent doctor --section encoding
```

## Acceptance

- Shell quoting is correct for all supported shells.
- UTF-8 paths and Chinese text are handled as normal.
- Terminal capability detection drives UTF-8 vs ASCII output.
- Paths with spaces always work.

## Commit Boundary

Commit only platform-io files and tests after verification passes. Do not add unrelated install behavior here.
