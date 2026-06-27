# Workflow Engine

## Goal

Provide resumable, inspectable workflows for planning, daily work, chapter production, revision, and export.

## Workflow Run Model

```json
{
  "run_id": "run-20260626-001",
  "project_slug": "demo_novel",
  "workflow_name": "chapter",
  "status": "running",
  "current_step": "retrieve_evidence",
  "data": {
    "volume_no": 1,
    "chapter_no": 3,
    "provider_role": "drafter"
  },
  "steps": []
}
```

## Step Result Model

```json
{
  "name": "retrieve_evidence",
  "status": "ok",
  "started_at": "2026-06-26T10:00:00",
  "ended_at": "2026-06-26T10:00:02",
  "artifacts": [
    "workspace/evidence_packs/demo_novel/chapter_003.json"
  ],
  "summary": "Retrieved 8 memory items and 4 ProseForge facts.",
  "error": ""
}
```

## Chapter Workflow Steps

1. `start_run`
2. `engine_status`
3. `chapter_pre`
4. `build_retrieval_intent`
5. `retrieve_evidence`
6. `write_evidence_pack`
7. `build_prompt_pack`
8. `draft_chapter`
9. `save_draft`
10. `chapter_post`
11. `chapter_review`
12. `rewrite_card`
13. `rewrite_draft`
14. `accept_revision`
15. `extract_memory`
16. `daily_closeout`
17. `finish_run`

## Resume Behavior

If a run fails at step 8:

- State file remains available.
- Prompt pack remains available.
- Evidence pack remains available.
- User can retry provider call.
- User can switch provider role.
- Workflow continues from `draft_chapter`, not from `chapter_pre`, unless forced.

## Artifact Rules

- Every step that produces a file must add the file path to `artifacts`.
- Drafts must be versioned.
- Evidence packs must be written before prompts.
- Prompt packs must be written before model calls.
- Review and accept reports must include underlying ProseForge command result.

## Workflow Acceptance Criteria

- Workflow state is saved after every step.
- Failed run can be loaded and inspected.
- Failed model call does not require rerunning retrieval.
- Failed ProseForge command preserves stdout and stderr.
- The user can run a dry-run mode through fake provider.
