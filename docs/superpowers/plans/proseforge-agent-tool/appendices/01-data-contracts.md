# Data Contracts

## Agent Config

```json
{
  "project_slug": "demo_novel",
  "project_title": "Demo Novel",
  "proseforge_root": "${PROSEFORGE_ROOT}",
  "proseforge_slot": "",
  "workspace_root": "${PROSEFORGE_AGENT_WORKSPACE:-.pf-agent}",
  "providers_config_path": "configs/providers.example.yaml",
  "default_volume_no": 1,
  "default_chapter_type": "normal",
  "daily_word_target": 2200
}
```

## Provider Spec

```json
{
  "name": "domestic_main",
  "kind": "openai_compatible",
  "model": "model-name",
  "options": {
    "base_url": "https://provider.example/v1",
    "api_key_env": "DOMESTIC_LLM_API_KEY",
    "timeout_seconds": 120
  }
}
```

## Generation Result

```json
{
  "text": "generated text",
  "provider": "domestic_main",
  "model": "model-name",
  "raw": {}
}
```

## Engine Result

```json
{
  "status": "ok",
  "payload": {},
  "stdout": "",
  "stderr": "",
  "returncode": 0,
  "command": []
}
```

## Memory Item

```json
{
  "id": 1,
  "project_id": 1,
  "scope": "novel",
  "memory_type": "canon_fact",
  "title": "血玉离身限制",
  "body": "血玉离开主角会失去灵识感应。",
  "source_kind": "chapter",
  "source_ref": "chapter:9",
  "entities_json": ["血玉", "主角"],
  "tags_json": ["血玉", "限制"],
  "importance": 5,
  "confidence": 0.9,
  "stability": "stable",
  "valid_from_chapter": 9,
  "valid_to_chapter": null,
  "use_count": 0,
  "last_used_at": null
}
```

## Retrieval Intent

```json
{
  "phase": "draft_chapter",
  "chapter_no": 12,
  "scene_goal": "审讯堂发现血玉旧案线索",
  "characters": ["主角", "师姐"],
  "plot_threads": ["旧案"],
  "reader_promises": ["血玉线索"],
  "risk_tags": ["canon", "continuity"]
}
```

## Evidence Pack

```json
{
  "status": "ok",
  "intent_id": "run-001",
  "query": "draft_chapter 审讯堂 血玉 主角 师姐 canon continuity",
  "must_keep": [],
  "useful_context": [],
  "risk_warnings": [],
  "degraded_reason": "",
  "retrieval_log_id": 1
}
```

## Workflow Run

```json
{
  "run_id": "run-001",
  "project_slug": "demo_novel",
  "workflow_name": "chapter",
  "status": "running",
  "current_step": "retrieve_evidence",
  "data": {},
  "steps": []
}
```

## Step Result

```json
{
  "name": "retrieve_evidence",
  "status": "ok",
  "started_at": "2026-06-26T00:00:00",
  "ended_at": "2026-06-26T00:00:01",
  "artifacts": [],
  "summary": "retrieved evidence",
  "error": ""
}
```
