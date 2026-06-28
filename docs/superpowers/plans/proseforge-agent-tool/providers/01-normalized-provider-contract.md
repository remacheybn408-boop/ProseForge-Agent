# Normalized Provider Contract

## Goal

Every model provider should look the same to the workflow, even when the provider uses different protocols.

## Core Provider Interface

```python
class LLMProvider(Protocol):
    name: str
    family: str
    protocol: str
    model: str

    def generate(self, request: ProviderRequest) -> ProviderResult:
        ...
```

## Provider Request

```json
{
  "request_id": "req-001",
  "role": "drafter",
  "messages": [
    {"role": "system", "content": "You are a professional novelist."},
    {"role": "user", "content": "Write chapter 3."}
  ],
  "input_text": "",
  "temperature": 0.7,
  "max_output_tokens": 4096,
  "stream": false,
  "response_format": "text",
  "tools": [],
  "extra": {}
}
```

## Provider Result

```json
{
  "request_id": "req-001",
  "provider": "deepseek_main",
  "family": "deepseek",
  "protocol": "openai_chat_completions",
  "model": "configured-model-id",
  "text": "chapter text",
  "reasoning_text": "",
  "tool_calls": [],
  "usage": {
    "input_tokens": 0,
    "output_tokens": 0,
    "total_tokens": 0
  },
  "raw": {},
  "warnings": []
}
```

## Protocol Types

| Protocol | Use |
| --- | --- |
| `openai_chat_completions` | `/chat/completions` shape |
| `openai_responses` | `/responses` shape |
| `anthropic_messages` | Anthropic Messages shape |
| `gemini_generate_content` | Gemini `generateContent` shape |
| `provider_native` | provider-specific fallback |
| `local_openai_compatible` | local OpenAI-compatible servers |

## Capability Flags

Each provider profile must declare:

```yaml
capabilities:
  text: true
  long_context: unknown
  streaming: unknown
  json_mode: unknown
  structured_output: unknown
  tool_calling: unknown
  reasoning_controls: unknown
  reasoning_text_return: unknown
  vision: unknown
  audio: unknown
  embeddings: false
  batch: unknown
```

Use `unknown` until verified by docs or capability probing.

## Error Contract

All provider adapters normalize errors:

```json
{
  "provider": "qwen_main",
  "error_type": "auth_error",
  "message": "missing DASHSCOPE_API_KEY",
  "retryable": false,
  "raw": {}
}
```

Error types:

- `auth_error`
- `rate_limit`
- `timeout`
- `invalid_request`
- `invalid_response`
- `provider_unavailable`
- `content_filter`
- `unknown`

## Acceptance

- Workflow code consumes only `ProviderRequest` and `ProviderResult`.
- Provider-specific fields go into `extra` or `raw`.
- Capability flags are visible in provider status.
- Unknown capabilities are not assumed.
