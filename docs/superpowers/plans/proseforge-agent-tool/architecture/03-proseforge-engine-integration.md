# ProseForge Engine Integration

## Purpose

The Agent must expose existing ProseForge functionality without duplicating the implementation. The safest first version calls the Codex wrapper scripts through subprocesses.

## Existing Engine Location

Expected default:

```text
$PROSEFORGE_ROOT
```

Required markers:

```text
$PROSEFORGE_ROOT\pyproject.toml
$PROSEFORGE_ROOT\database\schema.sql
$PROSEFORGE_ROOT\src\
$PROSEFORGE_ROOT\plugin\proseforge-codex\scripts\nf_project.py
$PROSEFORGE_ROOT\plugin\proseforge-codex\scripts\nf_pipeline.py
```

## Supported Engine Actions

### Project Actions

| Agent operation | Engine command |
| --- | --- |
| initialize workspace | `nf_project --action init` |
| status | `nf_project --action status` |
| create slot | `nf_project --action create` |
| list slots | `nf_project --action list` |
| add outline | `nf_project --action outline --sub-action add` |
| export | `nf_project --action export` |

### Pipeline Actions

| Agent operation | Engine command |
| --- | --- |
| chapter preparation | `nf_pipeline --action pre` |
| post-write gates | `nf_pipeline --action post` |
| review board | `nf_pipeline --action review` |
| batch post | `nf_pipeline --action batch` |
| volume report | `nf_pipeline --action volume` |
| rewrite card | `nf_pipeline --action rewrite` |
| accept revision | `nf_pipeline --action accept --ingest` |

## Adapter Rules

- Always pass `--project-root $PROSEFORGE_ROOT`.
- Always run subprocesses with `cwd` set to the ProseForge root.
- Capture stdout and stderr separately.
- Parse JSON stdout when possible.
- Preserve raw stdout when parsing fails.
- Never delete or modify ProseForge files outside engine commands.
- Never call `git reset`, `git checkout`, or destructive cleanup.

## Engine Result Shape

```json
{
  "status": "ok",
  "payload": {},
  "stdout": "",
  "stderr": "",
  "returncode": 0,
  "command": ["python", "..."]
}
```

## Smoke Tests

Safe smoke commands:

```powershell
python $PROSEFORGE_ROOT\plugin\proseforge-codex\scripts\nf_project.py --action status --project-root $PROSEFORGE_ROOT
```

Potentially mutating commands must be run only after a test workspace or demo slot is confirmed:

```powershell
python $PROSEFORGE_ROOT\plugin\proseforge-codex\scripts\nf_project.py --action init --project-root $PROSEFORGE_ROOT
```

## Integration Acceptance

- Adapter rejects paths that do not look like ProseForge.
- Adapter builds exact commands for every required action.
- Adapter records stdout, stderr, return code, parsed payload, and command.
- Workflow can call `status` without requiring a novel project.
- Chapter workflow can call `pre`, `post`, `review` through the same adapter.
