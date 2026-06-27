# Task 54: Uninstall And Data Retention

## Goal

Provide uninstall flows that distinguish binaries, shell integration, cache, logs, and user data.

## Agent Product Requirement

Users must be able to remove the tool without accidentally deleting novels, memory, or chats.

## Architecture Notes

`uninstall` plans removal as discrete, opt-in categories: binaries, shell integration, cache/logs, and user data. User data (novels, memory, chats, workflow runs) is preserved by default and only removed after an explicit confirmation. Planning is read-only and produces an action list; execution of any user-data deletion requires the `system_write` permission plus confirmation. It reuses `app_dirs` (Task 43) to classify paths.

Read before starting:

- ../architecture/02-system-architecture.md
- ../architecture/09-installation-and-native-platforms.md (Upgrade And Uninstall)
- 00-task-index.md

## Files

- Create `src/proseforge_agent/install/uninstall.py`
- Create `tests/test_uninstall_data_retention.py`
- Create `tests/fixtures/uninstall-and-data-retention/installed_layout.json`

## Interfaces / Contracts

- `UninstallPlanner(app_dirs).plan(remove_user_data: bool = False) -> UninstallPlan`.
- `UninstallPlan` groups actions by category: `binaries`, `shell_integration`, `cache_logs`, `user_data`.
- With `remove_user_data=False`, the `user_data` category is empty and a retained-paths note lists what is kept.
- Executing user-data deletion requires `system_write` permission and an explicit confirmation token.

## Data Flow

1. Classify installed paths into categories via `app_dirs`.
2. Build the action list for the requested categories.
3. Keep user data unless `remove_user_data=True`.
4. Mark user-data deletion as confirmation-required.
5. Return the `UninstallPlan` (no deletion during planning).

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_uninstall_data_retention.py::test_default_plan_preserves_user_data`**

```python
def test_default_plan_preserves_user_data(fake_app_dirs):
    plan = UninstallPlanner(fake_app_dirs).plan(remove_user_data=False)
    assert plan.user_data == []
    assert plan.retained_paths  # novels, memory, chats are listed as kept
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/test_uninstall_data_retention.py::test_default_plan_preserves_user_data -q
```

Expected: FAIL because `UninstallPlanner` and `UninstallPlan` are missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement `UninstallPlanner`, `UninstallPlan`, category classification, and confirmation gating.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/test_uninstall_data_retention.py::test_default_plan_preserves_user_data -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

```text
test_remove_user_data_requires_confirmation_token
test_binaries_and_shell_integration_can_be_removed_independently
test_cache_and_logs_removal_does_not_touch_user_data
test_planning_performs_no_deletion
test_chinese_project_paths_are_classified_as_user_data
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_uninstall_data_retention.py -q
pf-agent uninstall --plan
```

Expected: tests pass and `uninstall --plan` lists categories and the retained user data without deleting anything.

- [ ] **Step 7: Run cross-platform contract check**

```powershell
python -m pytest tests/test_uninstall_data_retention.py -q
```

Expected: PASS for simulated Windows, macOS, and Linux install layouts in the test file.

- [ ] **Step 8: Record commit boundary**

```powershell
git add src/proseforge_agent/install/uninstall.py tests/test_uninstall_data_retention.py tests/fixtures/uninstall-and-data-retention
git commit -m "feat: add uninstall data retention"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Cross-Platform Notes

- Path classification uses `app_dirs` on all three platforms.
- UTF-8 fixtures cover Chinese project paths classified as user data.
- No machine-specific absolute paths in the plan.

## Failure Modes To Prove

- User data is preserved by default.
- Deleting user data requires a confirmation token and `system_write`.
- Planning never deletes anything.
- Cache/log removal never touches user data.

## Verification

```powershell
python -m pytest tests/test_uninstall_data_retention.py -q
pf-agent uninstall --plan
```

## Acceptance

- Uninstall categories are explicit and independent.
- User data is preserved unless explicitly removed with confirmation.
- Planning is read-only.
- Reports list retained and removed paths.

## Commit Boundary

Commit only uninstall files and tests after verification passes. Do not perform real deletions in tests.
