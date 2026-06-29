# Task 174: Skill Specification And Registry

## Goal

Add a first-class skill specification and registry for procedural agent memory.

## Architecture Notes

Skills are reusable instructions, scripts, fixtures, and assets. They are not plugins with arbitrary runtime power unless explicitly granted through the plugin and permission model.

## Files

- Create `src/proseforge_agent/skills/`.
- Add tests in `tests/skills/test_skill_specification_registry.py`.
- Add fixtures under `tests/skills/fixtures/spec-registry/`.

## Interfaces / Contracts

- `SKILL.md` frontmatter includes name, description, triggers, version, permissions, files, and provenance.
- `SkillRegistry.discover(paths)` returns validated skill records.
- `pf-agent skills list`.

## TDD Steps

- [ ] Write failing test `tests/skills/test_skill_specification_registry.py::test_skill_registry_validates_frontmatter`.
- [ ] Run `python -m pytest tests/skills/test_skill_specification_registry.py::test_skill_registry_validates_frontmatter -q` and confirm failure.
- [ ] Implement skill parser, registry, validation, provenance, and list command.
- [ ] Run the targeted test and confirm pass.
- [ ] Add companion tests for missing fields, duplicate names, unsafe paths, version parsing, and disabled skills.
- [ ] Run `python -m pytest tests/skills/test_skill_specification_registry.py -q` and `python -m pytest -q`.
- [ ] Commit with `feat: add skill specification and registry`.

## Verification

```powershell
python -m pytest tests/skills/test_skill_specification_registry.py -q
pf-agent skills list
python -m pytest -q
```

## Acceptance

- Skills have a typed, validated local format.
- Registry discovery is deterministic and path-contained.
- Skills cannot silently request elevated permissions.
- Disabled or invalid skills are reported clearly.

## Commit Boundary

Commit only Task 174 skill spec, registry, tests, fixtures, and CLI wiring. Do not bundle adjacent task cards.

