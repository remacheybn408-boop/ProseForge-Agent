# Foreign Provider Matrix

## OpenAI / ChatGPT API

**Official source reviewed:** OpenAI API docs.

**Preferred protocols**

- `openai_responses` for new agentic workflows.
- `openai_chat_completions` for compatibility and provider parity.

**Default profiles**

```yaml
openai_responses_main:
  family: openai
  protocol: openai_responses
  kind: openai_responses
  base_url: "https://api.openai.com/v1"
  api_key_env: "OPENAI_API_KEY"
  model: "${OPENAI_MODEL}"

openai_chat_main:
  family: openai
  protocol: openai_chat_completions
  kind: openai_compatible
  base_url: "https://api.openai.com/v1"
  api_key_env: "OPENAI_API_KEY"
  model: "${OPENAI_CHAT_MODEL}"
```

**Acceptance**

- Responses adapter can parse `output_text`.
- Chat adapter can parse `choices[0].message.content`.
- Workflow can choose either protocol per role.

## Anthropic / Claude

**Official source reviewed:** Anthropic Messages API and Claude Code docs.

**Preferred protocol:** `anthropic_messages`.

**Default profile**

```yaml
claude_main:
  family: anthropic
  protocol: anthropic_messages
  kind: anthropic_native
  base_url: "https://api.anthropic.com/v1"
  api_key_env: "ANTHROPIC_API_KEY"
  model: "${ANTHROPIC_MODEL}"
```

**Acceptance**

- Adapter sends `x-api-key` and version header.
- Adapter parses text content blocks.
- Claude profile is preferred for `critic` and `planner` roles when configured.

## Google / Gemini

**Official source reviewed:** Gemini API docs and Gemini OpenAI compatibility docs.

**Preferred protocols**

- `gemini_generate_content` for native Gemini behavior.
- `openai_chat_completions` when using Google OpenAI compatibility.

**Default profiles**

```yaml
gemini_native_main:
  family: gemini
  protocol: gemini_generate_content
  kind: gemini_native
  base_url: "https://generativelanguage.googleapis.com/v1beta"
  api_key_env: "GEMINI_API_KEY"
  model: "${GEMINI_MODEL}"

gemini_openai_compatible:
  family: gemini
  protocol: openai_chat_completions
  kind: openai_compatible
  base_url: "https://generativelanguage.googleapis.com/v1beta/openai"
  api_key_env: "GEMINI_API_KEY"
  model: "${GEMINI_OPENAI_MODEL}"
```

**Acceptance**

- Native adapter parses `candidates`.
- OpenAI-compatible profile can use the shared adapter.
- Capability probe records structured output and tool support separately.

## xAI / Grok

**Official source reviewed:** xAI docs.

**Preferred protocols**

- `openai_responses` for xAI Responses API.
- `openai_chat_completions` for compatibility if needed.

**Default profile**

```yaml
grok_main:
  family: xai
  protocol: openai_responses
  kind: openai_responses
  base_url: "https://api.x.ai/v1"
  api_key_env: "XAI_API_KEY"
  model: "${XAI_MODEL}"
```

**Acceptance**

- Responses parser handles `output_text`.
- Profile can fall back to OpenAI-compatible chat when configured.
- Grok profile can be mapped to `researcher` or `critic` roles, but not required by default.

## Foreign Provider Acceptance Matrix

| Provider | Native protocol | Compatibility protocol | Required tests |
| --- | --- | --- | --- |
| OpenAI | Responses | Chat Completions | responses parse, chat parse |
| Anthropic | Messages | via some gateways only | message request, content block parse |
| Gemini | GenerateContent | OpenAI compatibility | native parse, compatible parse |
| Grok | Responses | Chat Completions | output_text parse, fallback parse |
