# Model Provider Adapters

## Goal

Make the workflow model-agnostic. The workflow asks for a role such as `drafter` or `critic`; provider config decides which model handles it.

## Provider Kinds

| Kind | Purpose |
| --- | --- |
| `fake` | deterministic tests without network |
| `openai_compatible` | OpenAI, OpenRouter, DeepSeek, Qwen-compatible, Kimi-compatible, Zhipu-compatible, SiliconFlow, local servers |
| `anthropic_native` | Anthropic-style messages API |
| `gemini_native` | Gemini-style generateContent API |

## Model Roles

| Role | Use |
| --- | --- |
| `planner` | phase plan, outline, market positioning |
| `drafter` | first draft prose |
| `rewriter` | targeted rewrite from task card |
| `critic` | review, contradiction search, risk analysis |
| `summarizer` | chapter summary, memory compaction |
| `extractor` | structured memory extraction |

## Provider Config Example

```yaml
default_provider: fake_main

providers:
  fake_main:
    kind: fake
    model: fake-model

  openai_main:
    kind: openai_compatible
    base_url: "https://api.openai.com/v1"
    api_key_env: "OPENAI_API_KEY"
    model: "gpt-4.1"
    timeout_seconds: 120

  domestic_main:
    kind: openai_compatible
    base_url: "${DOMESTIC_LLM_BASE_URL}"
    api_key_env: "DOMESTIC_LLM_API_KEY"
    model: "${DOMESTIC_LLM_MODEL}"
    timeout_seconds: 120

  local_main:
    kind: openai_compatible
    base_url: "http://localhost:11434/v1"
    api_key_env: "LOCAL_LLM_API_KEY"
    model: "qwen2.5"
    timeout_seconds: 300

  anthropic_main:
    kind: anthropic_native
    api_key_env: "ANTHROPIC_API_KEY"
    model: "claude-sonnet"

  gemini_main:
    kind: gemini_native
    api_key_env: "GEMINI_API_KEY"
    model: "gemini-pro"

model_roles:
  planner: openai_main
  drafter: domestic_main
  rewriter: domestic_main
  critic: anthropic_main
  summarizer: local_main
  extractor: openai_main
```

## Adapter Requirements

All providers return the same shape:

```python
GenerationResult(
    text="...",
    provider="openai_main",
    model="gpt-4.1",
    raw={...},
)
```

All providers accept the same call:

```python
provider.generate(
    messages=[
        {"role": "system", "content": "..."},
        {"role": "user", "content": "..."},
    ],
    temperature=0.7,
)
```

## Error Policy

- Missing API key raises `ProviderError`.
- Invalid response shape raises `ProviderError`.
- Network errors raise `ProviderError` with provider name.
- The workflow must save prompt packs before provider calls, so failed calls can be retried manually.

## Domestic And Local Provider Strategy

Many domestic providers and local servers expose OpenAI-compatible APIs. The first release should avoid hard-coding provider names where possible:

- Use `base_url`.
- Use `api_key_env`.
- Use `model`.
- Let users name providers freely.

Example provider names can include:

- `deepseek_main`
- `qwen_main`
- `kimi_main`
- `glm_main`
- `siliconflow_main`
- `openrouter_main`
- `local_ollama`
- `local_lmstudio`
- `local_vllm`

## Acceptance Criteria

- Tests can run with `fake` provider only.
- OpenAI-compatible adapter can be tested with injected transport.
- Native adapters can be tested with injected transport.
- Role routing is independent from workflow logic.
- Provider config can represent foreign, domestic, and local models.
