# Provider Routing Policy

## Goal

Route work by role and capability, not by hard-coded model name.

## Role Defaults

```yaml
model_roles:
  planner: openai_responses_main
  drafter: qwen_main
  rewriter: deepseek_main
  critic: claude_main
  summarizer: local_openai_compatible
  extractor: glm_main
  researcher: grok_main
  fallback: qwen_main
```

## Role Requirements

| Role | Required capabilities | Preferred traits |
| --- | --- | --- |
| planner | long context, reasoning | strong structure |
| drafter | long output, style stability | fluent Chinese prose |
| rewriter | instruction following | precise edits |
| critic | analysis, long context | strict risk detection |
| summarizer | cheap, stable text | concise output |
| extractor | JSON or structured output | schema adherence |
| researcher | web/search/tool support if available | source awareness |

## Routing Algorithm

1. Load role mapping.
2. Load provider profile.
3. Check provider is enabled.
4. Check required capability flags.
5. If capability is `false`, reject provider for role.
6. If capability is `unknown`, allow only when role policy permits unknown.
7. If provider call fails and role has fallback chain, retry next provider.
8. Record provider, model, protocol, and fallback reason in workflow state.

## Fallback Chains

```yaml
fallback_chains:
  planner: [openai_responses_main, claude_main, glm_main, qwen_main]
  drafter: [qwen_main, deepseek_main, doubao_main, minimax_main]
  rewriter: [deepseek_main, qwen_main, glm_main]
  critic: [claude_main, openai_responses_main, glm_main]
  summarizer: [local_openai_compatible, qwen_main, deepseek_main]
  extractor: [glm_main, openai_responses_main, qwen_main]
```

## Cost And Safety Policy

- Daily workbook generation should not require an LLM.
- Summarization should prefer cheap or local models.
- Drafting may use domestic models optimized for Chinese prose.
- Critical review may use a different model family from the drafter.
- Provider failures must not erase prompts or drafts.
- Fallback provider must receive the same evidence pack.

## Acceptance

- Router test proves role mapping.
- Router test proves fallback after simulated provider failure.
- Router test proves provider rejection when capability is false.
- Workflow report includes selected provider and fallback chain.
