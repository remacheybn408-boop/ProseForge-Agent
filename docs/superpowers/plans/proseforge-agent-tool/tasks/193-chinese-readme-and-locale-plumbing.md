# Task 193: Chinese README And Locale Plumbing / 中文 README 与 locale 基座

## Goal

Ship a fully translated `README.zh-CN.md`, wire a language switcher in the
main README, and establish the locale-plumbing pattern the project will use
for subsequent translated documents (CONTRIBUTING, SECURITY, docs/operators).

## Agent Product Requirement

The primary user base is Chinese-speaking novelists. The main README is
English-only. A well-crafted Chinese README is a bigger conversion driver
for this audience than any code feature we could add this month.

## Architecture Notes

Two things move together:

1. **Translated content** — `README.zh-CN.md`, a faithful translation of
   the current `README.md`. Preserve section anchors so cross-links from
   docs still work. Use the same terminology as the existing task cards
   (which are already partly bilingual). Do NOT machine-translate
   ProseForge / provider names.
2. **Locale switcher** — a small header block at the top of both READMEs:

   ```markdown
   > 🌐 [English](README.md) · [简体中文](README.zh-CN.md)
   ```

   Add a `docs/i18n/README.md` explaining the translation contract:
   which files are translated, what tone (informal 你 vs formal 您), and how
   updates propagate (source is `README.md`; translations follow within one
   release cycle).

Automated **drift detection** ensures the translated README doesn't
silently fall behind. A test computes a hash of each section header sequence
in `README.md` and compares with `README.zh-CN.md`; drift → test fails
with a diff.

Read before starting:

- README.md (current)
- 00-task-index.md

## Files

- Create `README.zh-CN.md`.
- Modify `README.md` — add locale switcher header.
- Create `docs/i18n/README.md`.
- Create `docs/i18n/glossary.md` — English → 简体中文 terminology map
  (Agent → 智能体; Provider → 模型提供方; Skill → 技能; Middleware → 中间件; …).
- Add tests in `tests/test_readme_localization.py`.
- Add fixtures under `tests/fixtures/chinese-readme-and-locale-plumbing/`:
  `expected_section_headers.txt`.

## Interfaces / Contracts

- `docs.i18n.drift.compare_readmes(english: Path, zh_cn: Path) -> DriftReport`
  — returns `DriftReport(matched: int, extra_in_source: list[str], extra_in_translation: list[str])`.
- The translated README MUST use the same H2/H3 header sequence as the
  English README (drift test enforces this).
- The switcher block is the FIRST line of both files, before the title.

## Data Flow

1. `pytest tests/test_readme_localization.py` extracts H2/H3 headers from
   both files.
2. Compares sequences; any divergence fails the test with a diff.
3. Glossary is not enforced by tests — it's a human contract in
   `docs/i18n/glossary.md` for future translators.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_readme_localization.py::test_readmes_have_matching_section_headers`**

```python
def test_readmes_have_matching_section_headers(repo_root):
    report = compare_readmes(repo_root / "README.md", repo_root / "README.zh-CN.md")
    assert not report.extra_in_source, f"Missing in translation: {report.extra_in_source}"
    assert not report.extra_in_translation, f"Not in source: {report.extra_in_translation}"
```

- [ ] **Step 2: Run the targeted test and confirm failure** (translated README doesn't exist yet).

- [ ] **Step 3: Translate the README, add switcher, add drift checker.**

- [ ] **Step 4: Run the targeted test and confirm pass.**

- [ ] **Step 5: Add companion tests**

```text
test_switcher_block_is_first_line_of_both_readmes
test_locale_switcher_links_use_relative_paths
test_glossary_covers_agent_provider_skill_middleware_workspace
test_chinese_readme_contains_no_lorem_ipsum_or_todo_markers
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_readme_localization.py -q
Get-Content README.zh-CN.md | Select-Object -First 3
```

- [ ] **Step 7: Run full repository verification**

```powershell
python -m pytest -q
```

- [ ] **Step 8: Record commit boundary**

```powershell
git add README.md README.zh-CN.md docs/i18n tests/test_readme_localization.py tests/fixtures/chinese-readme-and-locale-plumbing
git commit -m "docs: add chinese readme and locale plumbing"
```

## Cross-Platform Notes

- Both files use LF line endings and UTF-8 (no BOM).
- Anchor links (`[…](#some-section)`) rendered by GitHub differ by locale;
  the test only enforces H2/H3 sequence, not deep anchor equality.
- All fenced code blocks in the translated README stay verbatim — never
  translate commands, flags, or variable names.

## Failure Modes To Prove

- Adding a new section to `README.md` without translating fails the drift
  test with a clear header list.
- Broken UTF-8 in the translation fails at file read time.
- The switcher block missing from either file fails the switcher test.

## Verification

```powershell
python -m pytest tests/test_readme_localization.py -q
python -m pytest -q
```

## Acceptance

- `README.zh-CN.md` is a faithful translation with the same section
  sequence.
- Both READMEs open with the language switcher.
- `docs/i18n/glossary.md` is committed so future translators use the same
  terms.
- The drift test blocks silent divergence in future PRs.

## Commit Boundary

Commit only the two README files, `docs/i18n/`, the drift checker, tests,
and fixtures. Do not bundle community docs (Task 194) or the CLI config
example (Task 195) into this commit.
