# Risk Register

## Engineering Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| ProseForge root moves | Adapter cannot find engine | Explicit config and validation |
| ProseForge wrapper output is not JSON | Adapter parse fails | Preserve raw stdout |
| Windows path quoting issues | Commands fail | Use list-form subprocess arguments |
| UTF-8 console issues | Reports unreadable | Read/write files with UTF-8 and capture raw output |
| Provider API differences | Model calls fail | Provider kind abstraction and injected transport tests |
| Domestic endpoint changes | Config breaks | Do not hard-code domestic endpoints |
| Local model endpoint unavailable | Draft fails | Provider error with retry and prompt pack |
| Memory grows noisy | Bad retrieval | Ranking, compaction, source references |
| Retrieval misses canon | Continuity errors | ProseForge post/review still gate output |
| Workflow interruption | Lost work | Save state after every step |
| Draft overwritten | Lost writing | Versioned draft writer |
| Accept ingests bad rewrite | Novel damage | Empty rewrite block, accept result capture, guard rerun |

## Product Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Daily workbook too generic | User stops using it | Date, target, evidence, closeout required |
| Plan too large again | Execution slows | Keep index plus small files |
| Too many knobs | User confused | Ship examples and defaults |
| Model choice dominates workflow | Inconsistent output | Role-based routing |
| Agent becomes prompt-only | Loses professional workflow | Every model call must attach evidence and workflow state |

## Release Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Tests only cover happy path | Hidden failures | Add failure tests for config, provider, adapter, recovery |
| Real engine smoke mutates data | User data risk | Default smoke is status only |
| Generated local files committed | Repository bloat | Ignore workspace outputs later |
| Docs drift from commands | User confusion | CLI tests and docs audit before release |

## Risk Review Cadence

Review this file:

- After Task 03.
- After Task 07.
- After Task 13.
- Before Task 17 release hardening.
