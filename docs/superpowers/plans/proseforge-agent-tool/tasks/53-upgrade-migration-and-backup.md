# Task 53: Upgrade, Migration, And Backup

## Goal

Preserve user data across version upgrades and provide safe backups before migrations.

## Agent Product Requirement

An agent with memory and chats must not lose user history during updates.

## Architecture Notes

`migrations` runs schema and layout migrations for the workspace (agent.db, chats, memory, workflow runs, provider records) and always takes a backup before any destructive change. A failed migration restores from the backup and reports rollback steps; it never leaves the workspace half-migrated. It reuses `app_dirs` (Task 43) to locate data and the config schema version. It performs no provider calls.

Read before starting:

- ../architecture/02-system-architecture.md
- ../architecture/09-installation-and-native-platforms.md (Upgrade And Uninstall)
- 00-task-index.md

## Files

- Create `src/proseforge_agent/install/migrations.py`
- Create `tests/test_upgrade_migration_backup.py`
- Create `tests/fixtures/upgrade-migration-and-backup/workspace_v1/`

## Interfaces / Contracts

- `MigrationRunner(root).run(from_version, to_version) -> MigrationResult`.
- `MigrationResult` fields: `backup_path`, `migrated_files`, `from_version`, `to_version`, `warnings`, `rollback_steps`.
- A backup is created before any file is modified; `backup_path` always exists on success and on failure.
- On failure the runner restores from backup and returns `status="rolled_back"` with `rollback_steps`.

## Data Flow

1. Detect current and target schema/layout versions.
2. Create a timestamped backup of the data directory.
3. Apply ordered migration steps.
4. On error, restore from the backup.
5. Return a `MigrationResult` describing what changed or rolled back.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_upgrade_migration_backup.py::test_backup_is_created_before_any_file_is_modified`**

```python
def test_backup_is_created_before_any_file_is_modified(tmp_path):
    result = MigrationRunner(tmp_path).run(from_version="0.1.0", to_version="0.2.0")
    assert result.backup_path.exists()
    assert result.from_version == "0.1.0"
    assert result.to_version == "0.2.0"
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/test_upgrade_migration_backup.py::test_backup_is_created_before_any_file_is_modified -q
```

Expected: FAIL because `MigrationRunner` and `MigrationResult` are missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement `MigrationRunner`, `MigrationResult`, backup creation, ordered steps, and rollback.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/test_upgrade_migration_backup.py::test_backup_is_created_before_any_file_is_modified -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

```text
test_failed_migration_restores_from_backup_and_reports_rollback
test_upgrade_preserves_chats_memory_and_workflow_runs
test_no_op_when_versions_match
test_unknown_target_version_raises_configuration_error
test_chinese_content_survives_migration_round_trip
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_upgrade_migration_backup.py -q
pf-agent upgrade --check
```

Expected: tests pass and `upgrade --check` reports the backup path and pending migrations without applying them.

- [ ] **Step 7: Run cross-platform contract check**

```powershell
python -m pytest tests/test_upgrade_migration_backup.py -q
```

Expected: PASS for simulated Windows, macOS, and Linux data directories in the test file.

- [ ] **Step 8: Record commit boundary**

```powershell
git add src/proseforge_agent/install/migrations.py tests/test_upgrade_migration_backup.py tests/fixtures/upgrade-migration-and-backup
git commit -m "feat: add upgrade migration backup"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Cross-Platform Notes

- Backup and data paths are relative to the resolved app data directory.
- UTF-8 content (chats, memory) survives migration without corruption.
- No machine-specific absolute paths in reports.

## Failure Modes To Prove

- A failed migration restores from backup and reports rollback steps.
- No backup means no destructive change is attempted.
- Matching versions are a safe no-op.
- Chats, memory, and workflow runs are preserved.

## Verification

```powershell
python -m pytest tests/test_upgrade_migration_backup.py -q
pf-agent upgrade --check
```

## Acceptance

- A backup is taken before any destructive change.
- Failed migrations roll back cleanly.
- User data is preserved across upgrades.
- Reports list backup path and migrated files.

## Commit Boundary

Commit only migration files and tests after verification passes. Do not change live schema definitions outside this card's scope.
