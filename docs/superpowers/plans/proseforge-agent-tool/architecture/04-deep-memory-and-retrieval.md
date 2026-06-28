# Deep Memory And Retrieval

## Goal

Provide persistent memory that can be searched, linked, compacted, and automatically injected into planning, drafting, review, and revision.

## Memory Layers

| Layer | Scope | Stored In | Examples |
| --- | --- | --- | --- |
| L0 | Current run | workflow state JSON | selected provider, current task |
| L1 | Chapter | Agent memory and ProseForge DB | injuries, location, emotional state |
| L2 | Novel | Agent memory and ProseForge DB | canon facts, world rules, open hooks |
| L3 | Author | Agent DB | taste, forbidden tropes, preferred pacing |
| L4 | Market | Agent DB | genre expectations, audience promise |
| L5 | Research | Agent DB | external facts and reference notes |

## Memory Types

Required first-release types:

- `canon_fact`
- `character_state`
- `relationship_state`
- `world_rule`
- `plot_thread`
- `reader_promise`
- `writing_rule`
- `market_rule`
- `author_preference`
- `research_note`
- `review_finding`
- `daily_decision`

## Memory Item Fields

Each memory must carry:

- `project_id`
- `scope`
- `memory_type`
- `title`
- `body`
- `source_kind`
- `source_ref`
- `entities_json`
- `tags_json`
- `importance`
- `confidence`
- `stability`
- `valid_from_chapter`
- `valid_to_chapter`
- `use_count`
- `last_used_at`

## Retrieval Intent

Every retrieval begins from a structured intent:

```json
{
  "phase": "draft_chapter",
  "chapter_no": 12,
  "scene_goal": "审讯堂发现血玉旧案线索",
  "characters": ["主角", "师姐"],
  "plot_threads": ["旧案"],
  "reader_promises": ["血玉线索"],
  "risk_tags": ["canon", "continuity", "relationship"]
}
```

## Retrieval Sources

The router searches these sources in order:

1. Agent memory FTS5.
2. ProseForge `memories`.
3. ProseForge `characters`.
4. ProseForge `worldbuilding`.
5. ProseForge `plot_threads`.
6. ProseForge `reader_promises`.
7. ProseForge `writing_rules`.
8. ProseForge chapter summaries.
9. ProseForge chapter chunks.
10. Previous guard and review reports.

## Evidence Pack Shape

```json
{
  "status": "ok",
  "intent_id": "run-20260626-001",
  "query": "draft_chapter 审讯堂 血玉 主角 师姐 canon continuity",
  "must_keep": [
    {
      "title": "血玉不能离身",
      "text": "血玉离身会失去感应。",
      "source_ref": "memory:18",
      "memory_type": "canon_fact"
    }
  ],
  "useful_context": [],
  "risk_warnings": [],
  "degraded_reason": "",
  "retrieval_log_id": 12
}
```

## Ranking Policy

Final score should combine:

- Importance.
- Confidence.
- Recency.
- Entity overlap.
- Memory type priority.
- Exact query match.
- Chapter proximity.
- Source reliability.

First release can use a simple deterministic sort:

1. Must-keep memory types first.
2. Higher importance first.
3. Higher confidence first.
4. Newer update first.

## Conflict Policy

When two memories conflict:

- Do not silently choose one.
- Put both into `risk_warnings`.
- Mark evidence pack as `status: "needs_resolution"` when both are canon-level memories.
- Allow lower-risk conflicts to proceed only if they are not `canon_fact`, `world_rule`, `reader_promise`, or `relationship_state`.

## Compaction Policy

Compaction should run after chapter accept or after daily closeout:

- Merge duplicate review findings.
- Merge repeated daily decisions.
- Keep source references.
- Preserve high-confidence canon facts.
- Lower confidence when a fact is contradicted.
- Never delete source memories in first release; mark superseded later.

## Acceptance Criteria

- Memory can be added, searched, linked, and counted.
- Retrieval logs every query and source count.
- Evidence packs are written before model calls.
- Canon and reader promises appear in `must_keep`.
- Degraded retrieval is visible in daily workbook and workflow reports.
