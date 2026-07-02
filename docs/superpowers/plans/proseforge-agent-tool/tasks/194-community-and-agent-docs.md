# Task 194: Community And Agent Docs / 社区与代理文档

## Goal

Ship three foundational documents that every serious open-source project
needs and that AI agents increasingly rely on to safely operate a repo:
`CONTRIBUTING.md`, `SECURITY.md`, and `AGENTS.md`. Each is short, actionable,
and points to the actual code paths / tests / task cards in this repo.

## Agent Product Requirement

- **Humans** who want to submit a PR need to know the branch strategy
  ("每卡一分支"), how tests are named, the commit-message shape, and how
  to run the full suite locally.
- **Security researchers** need a private disclosure channel and a
  documented triage window.
- **Coding agents** (Claude Code, Cursor, Codex, this repo's own subagents)
  need a top-level `AGENTS.md` describing the repo's conventions,
  invariants, and forbidden actions — the same shape Anthropic and OpenAI
  are converging on as the industry norm.

## Architecture Notes

Every file uses the same pattern: one purpose line, then numbered rules
that reference concrete file paths so the reader can jump to code. No
aspirational prose.

`CONTRIBUTING.md`:

1. Local setup (`pip install -e ".[dev]"`, `python -m pytest -q`).
2. Branch strategy (feature branch per task card,
   `feat/task-<N>-<slug>`; matches the memory rule
   `[[git-workflow-branch-per-card]]`).
3. TDD requirement (RED → GREEN → refactor, one failing test named in the
   task card before any implementation).
4. Commit message shape (`feat: add <slug>` / `fix: …` / `docs: …` /
   `chore: …`; `Co-Authored-By: …` for AI-assisted commits).
5. PR checklist (`--no-ff` merge to main only after `pytest -q` is green
   on the feature branch AND after merge).
6. Where task cards live: link to `docs/superpowers/plans/proseforge-agent-tool/tasks/`.

`SECURITY.md`:

1. Supported versions (currently: the latest tag on `main`).
2. Reporting channel (private issue via GitHub Security Advisories; PGP
   key optional).
3. Triage SLA: acknowledge within 3 business days; fix or explain within
   30 days.
4. Scope: provider credential handling, MCP tool boundaries, execution
   environment isolation, secret redaction in observability/trajectory
   exports.
5. Out of scope: findings in the ProseForge engine itself
   (`$PROSEFORGE_ROOT`) — redirect to that project.

`AGENTS.md`:

1. Repo layout (one-line pointers to `src/proseforge_agent/*` and
   `docs/superpowers/plans/proseforge-agent-tool/tasks/`).
2. Coding conventions (`from __future__ import annotations` at top of every
   module, dataclasses for state, `@dataclass(frozen=True)` for value
   objects, no logging module use — use `EventBus` / `ObserverRegistry`).
3. Test conventions (tests live under `tests/`, name matches task-card
   slug, first assertion targets the RED behavior named in the card).
4. Forbidden actions (never write to `$PROSEFORGE_ROOT` from this repo,
   never bypass `PermissionPolicy`, never log secret material, never
   introduce a runtime dependency that is not already in
   `pyproject.toml`).
5. Where to find task cards, the commit-message shape, and the
   git-workflow-branch-per-card rule.

Read before starting:

- README.md
- docs/superpowers/plans/proseforge-agent-tool/tasks/00-task-index.md
- 186-default-chat-repl-on-bare-command.md
- 193-chinese-readme-and-locale-plumbing.md
- 00-task-index.md

## Files

- Create `CONTRIBUTING.md`.
- Create `SECURITY.md`.
- Create `AGENTS.md`.
- Create `docs/security/threat-model.md` (linked from SECURITY.md; single
  page listing the trust boundaries this project claims to enforce).
- Add tests in `tests/test_community_and_agent_docs.py`.
- Add fixtures under `tests/fixtures/community-and-agent-docs/`:
  `required_sections.json` — the section-header shape each doc must have.

## Interfaces / Contracts

- Each doc must start with a level-1 heading and a one-line description.
- `CONTRIBUTING.md` must reference `pyproject.toml`, `tests/`, and the
  task-cards directory.
- `SECURITY.md` must include the phrase "please do not open a public
  issue" and a reporting channel URL.
- `AGENTS.md` must list forbidden actions and the exact test command
  `python -m pytest -q`.

## Data Flow

1. `pytest tests/test_community_and_agent_docs.py` reads each doc.
2. Validates presence of required section headers from the fixture.
3. Validates presence of required literal phrases.
4. Emits a diff when any required element is missing.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_community_and_agent_docs.py::test_contributing_document_has_required_sections`**

```python
def test_contributing_document_has_required_sections(repo_root):
    text = (repo_root / "CONTRIBUTING.md").read_text(encoding="utf-8")
    for header in ["## Local Setup", "## Branch Strategy", "## TDD Requirement",
                   "## Commit Messages", "## PR Checklist"]:
        assert header in text, f"missing: {header}"
```

- [ ] **Step 2: Run the targeted test and confirm failure** (files don't exist yet).

- [ ] **Step 3: Write CONTRIBUTING, SECURITY, AGENTS, and the threat model
  page.**

- [ ] **Step 4: Run the targeted test and confirm pass.**

- [ ] **Step 5: Add companion tests**

```text
test_security_document_lists_reporting_channel_and_triage_sla
test_agents_document_lists_forbidden_actions
test_docs_reference_only_files_that_exist_in_repo
test_docs_use_utf8_no_bom
test_contributing_references_task_cards_directory
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_community_and_agent_docs.py -q
Get-Content CONTRIBUTING.md, SECURITY.md, AGENTS.md | Select-Object -First 30
```

- [ ] **Step 7: Run full repository verification**

```powershell
python -m pytest -q
```

- [ ] **Step 8: Record commit boundary**

```powershell
git add CONTRIBUTING.md SECURITY.md AGENTS.md docs/security tests/test_community_and_agent_docs.py tests/fixtures/community-and-agent-docs
git commit -m "docs: add contributing security and agents documents"
```

## Cross-Platform Notes

- All three docs use LF line endings and UTF-8 (no BOM).
- Fenced code blocks stay language-tagged (`powershell`, `bash`, `python`)
  so GitHub's syntax highlighting works.
- Do not use non-ASCII arrow / bullet glyphs that trip Windows console
  paste — keep to `->`, `-`, `*`.

## Failure Modes To Prove

- A dangling file reference (e.g., pointing at a task card that doesn't
  exist) fails `test_docs_reference_only_files_that_exist_in_repo`.
- A BOM at the top of any of the three docs fails `test_docs_use_utf8_no_bom`.
- Removing a required section from any doc fails the section test with a
  precise header name.

## Verification

```powershell
python -m pytest tests/test_community_and_agent_docs.py -q
python -m pytest -q
```

## Acceptance

- Newcomer human contributors and agent contributors can both onboard from
  `AGENTS.md` + `CONTRIBUTING.md` alone.
- Security reporters have a clear private channel and an SLA.
- The threat model page names each trust boundary the project claims,
  enabling later `pf-agent doctor --section security` cross-checks.

## Commit Boundary

Commit only the three top-level docs, the threat model page, tests, and
fixtures. Do not bundle the CLI config example (Task 195), Chinese
translation of these docs (a future card), or additional docs.
