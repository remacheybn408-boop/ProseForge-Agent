# Task 178: Skill Usage Analytics And Safety Audit

## Goal

Track skill usage, effectiveness signals, failures, and safety audit findings.

## Architecture Notes

Analytics are local and privacy-preserving by default. They support quality improvement and debugging without exporting user data unless a future explicit integration opts in.

## Files

- Create `src/proseforge_agent/skills/usage.py`.
- Create `src/proseforge_agent/skills/audit.py`.
- Add tests in `tests/skills/test_skill_usage_analytics_safety_audit.py`.

## Interfaces / Contracts

- `SkillUsageRecord` stores skill id, version, trigger, outcome, duration, errors, and redacted trace refs.
- `pf-agent skills usage --skill <id>`
- `pf-agent skills audit`.

## TDD Steps

- [ ] Write failing test `tests/skills/test_skill_usage_analytics_safety_audit.py::test_usage_record_redacts_private_inputs`.
- [ ] Run `python -m pytest tests/skills/test_skill_usage_analytics_safety_audit.py::test_usage_record_redacts_private_inputs -q` and confirm failure.
- [ ] Implement usage records, summaries, audit checks, and CLI reports.
- [ ] Run the targeted test and confirm pass.
- [ ] Add companion tests for failure outcomes, disabled skills, unsafe instructions, stale versions, and support-bundle export.
- [ ] Run `python -m pytest tests/skills/test_skill_usage_analytics_safety_audit.py -q` and `python -m pytest -q`.
- [ ] Commit with `feat: add skill usage analytics and safety audit`.

## Verification

```powershell
python -m pytest tests/skills/test_skill_usage_analytics_safety_audit.py -q
pf-agent skills audit
python -m pytest -q
```

## Acceptance

- Skill usage is inspectable without leaking private inputs.
- Audit flags unsafe or stale skills.
- Reports are deterministic and support-bundle compatible.
- Analytics do not require network access.

## Commit Boundary

Commit only Task 178 skill usage/audit files, tests, fixtures, and CLI wiring. Do not bundle adjacent task cards.

