# Task 191: .env Support And .env.example / .env 支持与示例

## Goal

Read a `.env` file (KEY=value pairs) from the project root at process start
and populate `os.environ` with any keys that are not already set, so users
can drop API keys into a familiar file instead of exporting shell variables.
Ship a `.env.example` documenting every recognized key.

## Agent Product Requirement

`.env` is the de-facto standard for "I have secrets to give this tool".
Every AI CLI (Codex, Aider, Hermes, Claude Code) supports it. Requiring
users to `export TWINE_PASSWORD=…` or edit YAML is a friction point,
especially on Windows where `setx` behaves unexpectedly and existing shell
sessions don't see new values.

## Architecture Notes

Implement a tiny stdlib-only `.env` loader — do NOT add `python-dotenv` as
a dependency. The parser handles:

- `KEY=value` (unquoted, no interpolation)
- `KEY="value with spaces"` (double-quoted, unescaped)
- `KEY='value'` (single-quoted, literal)
- `# comment` lines and blank lines
- Trailing comments after unquoted values are NOT stripped (POSIX shell
  behavior) — the entire suffix is the value.

**Load precedence** (higher wins):

1. Existing `os.environ` — never overridden.
2. `.env.local` in project root.
3. `.env` in project root.
4. `<AppDirs.config_dir>/proseforge-agent.env` — machine-level defaults.

The loader is called from `_bootstrap.install()` (Task 190) so it runs
before any provider factory reads env vars. `.env.example` lives at repo
root and documents every recognized key with a one-line comment.

Read before starting:

- 190-windows-utf8-early-bootstrap.md
- 45-native-secret-storage.md
- 00-task-index.md

## Files

- Create `src/proseforge_agent/config/dotenv.py` (stdlib-only parser +
  loader).
- Modify `src/proseforge_agent/_bootstrap.py` to invoke
  `dotenv.load_default_files()` after stream reconfiguration.
- Create `.env.example` at repo root.
- Add `.env` and `.env.local` to `.gitignore` (verify not already present).
- Add tests in `tests/test_dotenv_support.py`.
- Add fixtures under `tests/fixtures/dotenv-support/`:
  `simple.env`, `quoted.env`, `precedence_env`, `precedence_env_local`,
  `machine.env`.

## Interfaces / Contracts

- `DotenvLoader(paths: list[Path]).parse_one(path) -> dict[str, str]`.
- `DotenvLoader.load(override: bool = False) -> dict[str, str]` — merges the
  parsed dicts into `os.environ` (never overriding by default) and returns
  the resulting `{key: source_path}` audit map.
- `DotenvLoader.load_default_files() -> dict[str, str]` — resolves
  `.env`, `.env.local`, and `<AppDirs.config_dir>/proseforge-agent.env`
  in precedence order.
- `.env.example` — every documented key must appear here with a comment
  above it. Failing that, the test `test_env_example_covers_every_documented_key` fails.

## Data Flow

1. Process start → `_bootstrap.install()` → `dotenv.load_default_files()`.
2. Loader resolves the ordered list of files, reads each, parses each.
3. Merges into `os.environ` without overriding preexisting vars.
4. Records the source of each key in `_bootstrap.STATE["dotenv"]`.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_dotenv_support.py::test_dotenv_loader_populates_env_without_overriding`**

```python
def test_dotenv_loader_populates_env_without_overriding(monkeypatch, tmp_path):
    monkeypatch.setenv("EXISTING", "keep-me")
    monkeypatch.delenv("NEW_KEY", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("EXISTING=override\nNEW_KEY=hello\n", encoding="utf-8")

    audit = DotenvLoader([env_file]).load()

    assert os.environ["EXISTING"] == "keep-me"
    assert os.environ["NEW_KEY"] == "hello"
    assert audit["NEW_KEY"].endswith(".env")
```

- [ ] **Step 2: Run the targeted test and confirm failure.**

- [ ] **Step 3: Implement the parser and loader; wire into `_bootstrap`.**

- [ ] **Step 4: Run the targeted test and confirm pass.**

- [ ] **Step 5: Add companion tests**

```text
test_dotenv_parser_handles_quoted_values
test_dotenv_parser_handles_comments_and_blank_lines
test_dotenv_parser_preserves_trailing_hash_in_unquoted_value
test_dotenv_precedence_prefers_env_local_over_env
test_dotenv_machine_env_is_lowest_precedence
test_dotenv_never_reads_files_outside_declared_list
test_env_example_covers_every_documented_key
test_dotenv_missing_files_are_silent
test_dotenv_bad_syntax_reports_line_but_does_not_raise
```

- [ ] **Step 6: Run subsystem verification**

```powershell
Copy-Item .env.example .env
Add-Content .env "TWINE_PASSWORD=pypi-fake"
pf-agent release publish --repository testpypi --dry-run
# → uses TWINE_PASSWORD from .env
Remove-Item .env
```

- [ ] **Step 7: Run full repository verification**

```powershell
python -m pytest -q
```

- [ ] **Step 8: Record commit boundary**

```powershell
git add src/proseforge_agent/config/dotenv.py src/proseforge_agent/_bootstrap.py .env.example .gitignore tests/test_dotenv_support.py tests/fixtures/dotenv-support
git commit -m "feat: add .env file support"
```

## Cross-Platform Notes

- `.env.example` uses LF line endings (`.gitattributes` should already
  enforce this). If not, add an entry for `*.env text eol=lf`.
- On Windows, `<AppDirs.config_dir>/proseforge-agent.env` lives under
  `%APPDATA%\ProseForge Agent\`.
- `.env` MUST be added to `.gitignore` in the same commit.

## Failure Modes To Prove

- A `.env` file with 3 valid lines and 1 malformed line loads the 3 valid
  keys and reports the malformed line number in `warnings`.
- Existing `os.environ` values are never overridden by default.
- `.env.local` overrides `.env` at load time.
- Missing files are silent; missing containing directory does not raise.
- Files containing NUL bytes are rejected with an unambiguous error.

## Verification

```powershell
python -m pytest tests/test_dotenv_support.py -q
python -m pytest -q
```

## Acceptance

- Users can drop `TWINE_PASSWORD=…`, `OPENAI_API_KEY=…`, and other
  documented keys into `.env` and have them picked up on next `pf-agent`
  invocation.
- `.env` and `.env.local` are gitignored; only `.env.example` is
  committed.
- `.env.example` documents every recognized environment key referenced in
  the codebase (enforced by the coverage test).

## Commit Boundary

Commit only the parser, loader, bootstrap glue, `.env.example`,
`.gitignore` update, tests, and fixtures. Do not bundle the Docker
distribution (Task 192) or docs (193/194) into this commit.
