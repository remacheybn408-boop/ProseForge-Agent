# Task 175: Skill Hub Install And Sync

## Goal

Add skill hub installation, update, remove, and sync planning.

## Architecture Notes

Remote skill installation is high-risk. It must support dry-run previews, provenance records, checksums, permission review, and rollback without executing skill code during install.

## Files

- Create `src/proseforge_agent/skills/hub.py`.
- Create `src/proseforge_agent/skills/install.py`.
- Add tests in `tests/skills/test_skill_hub_install_sync.py`.

## Interfaces / Contracts

- `pf-agent skills search <query>`
- `pf-agent skills install <id> --dry-run`
- `pf-agent skills update --all --dry-run`
- Install plans include source, version, files, checksum, requested permissions, and rollback plan.

## TDD Steps

- [ ] Write failing test `tests/skills/test_skill_hub_install_sync.py::test_install_dry_run_reports_permissions_and_checksum`.
- [ ] Run `python -m pytest tests/skills/test_skill_hub_install_sync.py::test_install_dry_run_reports_permissions_and_checksum -q` and confirm failure.
- [ ] Implement fake hub client, install plan, checksum validation, rollback metadata, and CLI dry-run.
- [ ] Run the targeted test and confirm pass.
- [ ] Add companion tests for update, remove, corrupted package, permission denial, and offline cache.
- [ ] Run `python -m pytest tests/skills/test_skill_hub_install_sync.py -q` and `python -m pytest -q`.
- [ ] Commit with `feat: add skill hub install and sync`.

## Verification

```powershell
python -m pytest tests/skills/test_skill_hub_install_sync.py -q
pf-agent skills install demo-skill --dry-run --provider fake
python -m pytest -q
```

## Acceptance

- Skill install/update/remove can be previewed before writing.
- Provenance and checksums are persisted.
- Permission changes require explicit approval.
- Offline cache behavior is deterministic.

## Commit Boundary

Commit only Task 175 skill hub, install/sync, tests, fixtures, and CLI wiring. Do not bundle adjacent task cards.

