# Task 58: Operator Diagnostics And Support Bundle

## Goal

Create a redacted support bundle for install, provider, chat, memory, and workflow problems.

## Agent Product Requirement

When something breaks across platforms, users need one artifact they can share safely.

## Architecture Notes

`support_bundle` assembles one shareable archive from existing sources: the doctor report (Task 42), recent event trace ids (Task 40), provider statuses, config *shape* (not values), and OS info. Redaction is mandatory and on by default: no secret values, no full absolute user paths. The builder is read-only over the workspace and reuses the doctor and event bus rather than re-collecting their data.

Read before starting:

- ../architecture/02-system-architecture.md
- ../architecture/09-installation-and-native-platforms.md (Doctor Checks)
- 00-task-index.md

## Files

- Create `src/proseforge_agent/install/support_bundle.py`
- Create `tests/test_support_bundle.py`
- Create `tests/fixtures/operator-diagnostics-and-support-bundle/sample_sources.json`

## Interfaces / Contracts

- `SupportBundleBuilder(root, doctor, event_bus).build(redact: bool = True) -> SupportBundle`.
- `SupportBundle` fields: `bundle_path`, `included` (doctor report, logs, trace ids, provider status, config shape, os info), `redaction_report`.
- With `redact=True` (default), no secret value and no absolute user path appears in any included file.
- The builder writes only the bundle; it never mutates source data.

## Data Flow

1. Collect the doctor report and recent trace ids.
2. Gather provider statuses and config shape (keys only).
3. Add OS/architecture info.
4. Run redaction over every included file.
5. Write the bundle and a redaction report.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_support_bundle.py::test_bundle_redacts_secrets_and_includes_trace_ids`**

```python
def test_bundle_redacts_secrets_and_includes_trace_ids(tmp_path, fake_doctor, fake_event_bus):
    bundle = SupportBundleBuilder(tmp_path, fake_doctor, fake_event_bus).build(redact=True)
    text = bundle.bundle_path.read_text(encoding="utf-8")
    assert "sk-" not in text  # no secret material
    assert bundle.included["trace_ids"]
    assert bundle.redaction_report
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/test_support_bundle.py::test_bundle_redacts_secrets_and_includes_trace_ids -q
```

Expected: FAIL because `SupportBundleBuilder` and `SupportBundle` are missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement `SupportBundleBuilder`, `SupportBundle`, source collection, and redaction.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/test_support_bundle.py::test_bundle_redacts_secrets_and_includes_trace_ids -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

```text
test_config_shape_includes_keys_but_not_values
test_absolute_user_paths_are_redacted_to_placeholders
test_builder_does_not_mutate_source_data
test_bundle_includes_doctor_report_and_provider_status
test_chinese_paths_are_redacted_without_corruption
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_support_bundle.py -q
pf-agent support bundle --redact
```

Expected: tests pass and the command writes a redacted bundle and prints its path.

- [ ] **Step 7: Run cross-platform contract check**

```powershell
python -m pytest tests/test_support_bundle.py -q
```

Expected: PASS for simulated Windows, macOS, and Linux source layouts in the test file.

- [ ] **Step 8: Record commit boundary**

```powershell
git add src/proseforge_agent/install/support_bundle.py tests/test_support_bundle.py tests/fixtures/operator-diagnostics-and-support-bundle
git commit -m "feat: add operator diagnostics support bundle"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Cross-Platform Notes

- Redaction replaces absolute user paths with placeholders on all platforms.
- UTF-8 content is preserved through redaction.
- Bundle paths are relative to the workspace.

## Failure Modes To Prove

- No secret value appears in any bundle file when redaction is on.
- Config shape includes keys but never values.
- Absolute user paths are redacted to placeholders.
- The builder never mutates source data.

## Verification

```powershell
python -m pytest tests/test_support_bundle.py -q
pf-agent support bundle --redact
```

## Acceptance

- One shareable, redacted bundle is produced.
- It reuses the doctor report and event trace ids.
- Secrets and absolute paths are redacted by default.
- The builder is read-only over sources.

## Commit Boundary

Commit only support-bundle files and tests after verification passes. Do not change doctor or event bus internals here.
