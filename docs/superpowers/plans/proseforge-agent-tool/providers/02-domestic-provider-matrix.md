# Domestic Provider Matrix

## Goal

Support common domestic models as first-class profiles, with provider-specific notes, required environment variables, protocol choices, and acceptance checks.

## DeepSeek

**Official source reviewed:** DeepSeek API docs.

**Primary protocol:** OpenAI-compatible Chat Completions.

**Also noted:** DeepSeek docs state API compatibility with OpenAI and Anthropic formats.

**Default profile**

```yaml
deepseek_main:
  family: deepseek
  protocol: openai_chat_completions
  kind: openai_compatible
  base_url: "https://api.deepseek.com"
  api_key_env: "DEEPSEEK_API_KEY"
  model: "${DEEPSEEK_MODEL}"
  capabilities:
    text: true
    streaming: true
    reasoning_controls: true
    tool_calling: true
    json_mode: true
```

**Acceptance**

- Request shape test builds `/chat/completions`.
- Extra body can pass reasoning/thinking controls.
- Response parser handles `choices[0].message.content`.
- Profile supports role mapping for `planner`, `drafter`, `rewriter`, `critic`.

## Qwen / DashScope / Alibaba Model Studio

**Official source reviewed:** Alibaba Cloud Model Studio Qwen API docs.

**Primary protocol:** OpenAI-compatible Chat Completions.

**Other protocols:** OpenAI-compatible Responses, Anthropic-compatible Messages, DashScope native.

**Default profile**

```yaml
qwen_main:
  family: qwen
  protocol: openai_chat_completions
  kind: openai_compatible
  base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
  api_key_env: "DASHSCOPE_API_KEY"
  model: "qwen-plus"
  capabilities:
    text: true
    streaming: true
    structured_output: unknown
    tool_calling: unknown
    vision: provider_model_dependent
```

**Regional profile**

```yaml
qwen_workspace_cn_beijing:
  family: qwen
  protocol: openai_chat_completions
  kind: openai_compatible
  base_url: "https://${DASHSCOPE_WORKSPACE_ID}.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
  api_key_env: "DASHSCOPE_API_KEY"
  model: "qwen-plus"
```

**Acceptance**

- Profile supports default compatible endpoint.
- Profile supports workspace regional endpoint.
- Docs warn that some models or modalities require DashScope native.
- Capability probe records model-specific support.

## GLM / Zhipu AI

**Official source reviewed:** Zhipu GLM OpenAI API compatibility docs and HTTP API docs.

**Primary protocol:** OpenAI-compatible Chat Completions.

**Coding plan protocols:** OpenAI Chat Completion and Anthropic Message endpoints.

**Default profile**

```yaml
glm_main:
  family: glm
  protocol: openai_chat_completions
  kind: openai_compatible
  base_url: "https://open.bigmodel.cn/api/paas/v4"
  api_key_env: "ZHIPU_API_KEY"
  model: "glm-5.2"
  capabilities:
    text: true
    streaming: true
    long_context: provider_model_dependent
    tool_calling: unknown
```

**Coding-plan profile**

```yaml
glm_coding_plan:
  family: glm
  protocol: openai_chat_completions
  kind: openai_compatible
  base_url: "https://api.z.ai/api/coding/paas/v4"
  api_key_env: "ZAI_API_KEY"
  model: "glm-5.2"
```

**Acceptance**

- Standard GLM profile and Coding Plan profile are separate.
- Config validation prevents mixing base URLs.
- Response parser handles standard OpenAI-compatible response.

## Xiaomi MiMo

**Official source reviewed:** Xiaomi MiMo API docs and MiMo model-provider guide.

**Primary protocol:** OpenAI-compatible Chat Completions.

**Also noted:** MiMo docs describe OpenAI- and Anthropic-compatible APIs.

**Default profile**

```yaml
mimo_main:
  family: mimo
  protocol: openai_chat_completions
  kind: openai_compatible
  base_url: "${MIMO_BASE_URL}"
  api_key_env: "MIMO_API_KEY"
  model: "${MIMO_MODEL}"
  capabilities:
    text: true
    streaming: unknown
    long_context: provider_model_dependent
    vision: provider_model_dependent
    audio: provider_model_dependent
```

**Acceptance**

- Default endpoint can be configured from official MiMo docs; operator may override `MIMO_BASE_URL` when account type or region requires it.
- Profile can switch to Anthropic-compatible protocol later.
- Capability probe records which MiMo model supports text, vision, audio, and reasoning content.

## MiniMax

**Official source reviewed:** MiniMax API docs.

**Primary protocol:** OpenAI-compatible Chat Completions.

**Also noted:** MiniMax docs expose OpenAI-style and Anthropic-style text APIs; MiniMax-M3 has provider-specific multimodal and thinking parameters.

**Default profile**

```yaml
minimax_main:
  family: minimax
  protocol: openai_chat_completions
  kind: openai_compatible
  base_url: "https://api.minimax.io/v1"
  api_key_env: "MINIMAX_API_KEY"
  model: "MiniMax-M3"
  capabilities:
    text: true
    streaming: true
    reasoning_controls: true
    vision: provider_model_dependent
    video_input: provider_model_dependent
```

**Acceptance**

- Profile handles `/v1/chat/completions`.
- Extra provider parameters can be passed through `extra_body`.
- Tests prove unknown MiniMax fields do not break normalized result.

## Doubao / Volcengine Ark

**Official source reviewed:** Volcengine Ark docs.

**Primary protocol:** OpenAI-compatible SDK / Chat API.

**Also available:** Responses API and Ark-specific model management.

**Default profile**

```yaml
doubao_main:
  family: doubao
  protocol: openai_chat_completions
  kind: openai_compatible
  base_url: "https://ark.cn-beijing.volces.com/api/v3"
  api_key_env: "ARK_API_KEY"
  model: "${DOUBAO_MODEL}"
  capabilities:
    text: true
    streaming: true
    reasoning_controls: provider_model_dependent
    vision: provider_model_dependent
    structured_output: unknown
```

**Acceptance**

- Profile supports Ark OpenAI-compatible base URL.
- Model name is user-provided because Ark uses endpoints and model IDs that may vary by account.
- `responses` protocol can be added without changing workflow roles.

## Domestic Provider Acceptance Matrix

| Provider | Profile file | Request shape test | Response parse test | Capability probe | Real smoke optional |
| --- | --- | --- | --- | --- | --- |
| DeepSeek | required | required | required | required | optional |
| Qwen | required | required | required | required | optional |
| GLM | required | required | required | required | optional |
| MiMo | required | required | required | required | optional |
| MiniMax | required | required | required | required | optional |
| Doubao | required | required | required | required | optional |
