# Provider Verification And Acceptance

## Certification Pipeline

Every provider goes through these checks:

1. Documentation profile.
2. Config validation.
3. Request-shape test.
4. Response-parse test.
5. Error normalization test.
6. Capability probe.
7. Fake workflow role test.
8. Optional real smoke test.

## Request-Shape Test

Must verify:

- Correct URL.
- Correct auth header.
- Correct model field.
- Correct message or input field.
- Correct stream flag.
- Correct provider-specific extra fields.

## Response-Parse Test

Must verify:

- Text extraction.
- Reasoning text extraction if exposed.
- Tool calls extraction if exposed.
- Usage extraction if exposed.
- Raw payload preservation.

## Capability Probe

Capability probe sends safe minimal prompts when the user enables real API testing:

| Capability | Probe |
| --- | --- |
| text | ask for one sentence |
| streaming | stream one sentence |
| JSON | ask for strict JSON |
| tool calling | offer a no-op tool |
| reasoning controls | enable provider-specific thinking field |
| long context | send a synthetic long prompt under threshold |

## Real Smoke Test Policy

Real smoke tests are optional because they require user API keys.

Command shape:

```powershell
pf-agent provider smoke --provider deepseek_main --config configs/agent.yaml
```

Smoke output:

```json
{
  "provider": "deepseek_main",
  "status": "ok",
  "protocol": "openai_chat_completions",
  "model": "configured-model-id",
  "latency_ms": 1200,
  "usage": {},
  "warnings": []
}
```

## Acceptance Levels

| Level | Required evidence |
| --- | --- |
| `profiled` | provider matrix entry and config profile |
| `shape_tested` | request and response unit tests |
| `smoke_tested` | user-key real call result |
| `workflow_tested` | provider completes a role in fake or demo workflow |
| `certified` | all above plus fallback test and docs refresh date |

## Documentation Refresh

Provider docs should be refreshed before release and then monthly. Record:

- Date checked.
- Official source URL.
- Base URL.
- Protocols supported.
- Model naming rule.
- Known unsupported features.
