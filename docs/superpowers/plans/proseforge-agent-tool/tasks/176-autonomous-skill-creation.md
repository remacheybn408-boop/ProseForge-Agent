# Task 176: Autonomous Skill Creation

## Goal

Allow the agent to propose new skills from repeated or complex tasks without automatically enabling them.

## Architecture Notes

Autonomous skill creation writes candidates. Human or operator approval is required before a skill becomes enabled. The system must preserve source traces and avoid copying secrets or private project text into reusable skills.

## Files

- Create `src/proseforge_agent/skills/creation.py`.
- Add tests in `tests/skills/test_autonomous_skill_creation.py`.
- Add fixtures under `tests/skills/fixtures/skill-creation/`.

## Interfaces / Contracts

- `SkillCandidate` includes trigger, purpose, instructions, source trace ids, redaction status, and approval state.
- `pf-agent skills candidates list`
- `pf-agent skills candidates approve <id> --dry-run`.

## TDD Steps

- [ ] Write failing test `tests/skills/test_autonomous_skill_creation.py::test_skill_candidate_is_not_enabled_by_default`.
- [ ] Run `python -m pytest tests/skills/test_autonomous_skill_creation.py::test_skill_candidate_is_not_enabled_by_default -q` and confirm failure.
- [ ] Implement candidate extraction, redaction, persistence, and approval preview.
- [ ] Run the targeted test and confirm pass.
- [ ] Add companion tests for secret redaction, duplicate candidates, source trace links, approval workflow, and rejection.
- [ ] Run `python -m pytest tests/skills/test_autonomous_skill_creation.py -q` and `python -m pytest -q`.
- [ ] Commit with `feat: add autonomous skill creation`.

## Verification

```powershell
python -m pytest tests/skills/test_autonomous_skill_creation.py -q
pf-agent skills candidates list
python -m pytest -q
```

## Acceptance

- The agent can propose skill candidates from trace evidence.
- Candidates are not enabled automatically.
- Private project text and secrets are redacted from reusable instructions.
- Approval produces a dry-run install plan first.

## Commit Boundary

Commit only Task 176 skill creation files, tests, fixtures, and CLI wiring. Do not bundle adjacent task cards.

