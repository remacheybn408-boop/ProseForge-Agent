# Task 177: Skill Self Improvement And Provenance

## Goal

Allow skills to propose safe revisions based on use outcomes while preserving provenance and review history.

## Architecture Notes

Skill self-improvement must produce patch proposals, not direct edits to enabled skills. Review history links old version, proposed version, usage evidence, and operator decision.

## Files

- Create `src/proseforge_agent/skills/improvement.py`.
- Extend provenance models under `src/proseforge_agent/skills/`.
- Add tests in `tests/skills/test_skill_self_improvement_provenance.py`.

## Interfaces / Contracts

- `SkillRevisionCandidate` includes skill id, base version, proposed version, diff, evidence refs, risk flags, and approval state.
- `pf-agent skills improve <skill-id> --dry-run`
- Approved revisions create new versions without deleting old versions.

## TDD Steps

- [ ] Write failing test `tests/skills/test_skill_self_improvement_provenance.py::test_revision_candidate_preserves_base_version`.
- [ ] Run `python -m pytest tests/skills/test_skill_self_improvement_provenance.py::test_revision_candidate_preserves_base_version -q` and confirm failure.
- [ ] Implement revision candidates, diff generation, provenance links, and dry-run CLI.
- [ ] Run the targeted test and confirm pass.
- [ ] Add companion tests for rejected revisions, unsafe permission escalation, duplicate evidence, rollback, and audit export.
- [ ] Run `python -m pytest tests/skills/test_skill_self_improvement_provenance.py -q` and `python -m pytest -q`.
- [ ] Commit with `feat: add skill self improvement provenance`.

## Verification

```powershell
python -m pytest tests/skills/test_skill_self_improvement_provenance.py -q
pf-agent skills improve demo-skill --dry-run
python -m pytest -q
```

## Acceptance

- Skills propose revisions as reviewable candidates.
- Provenance links every revision to evidence and decision.
- Permission escalation is blocked unless explicitly reviewed.
- Previous versions remain recoverable.

## Commit Boundary

Commit only Task 177 skill improvement/provenance files, tests, fixtures, and CLI wiring. Do not bundle adjacent task cards.

