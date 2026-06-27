# Provider Adaptation Index

## Goal

Model adaptation must be supplier-level, not just abstract. ProseForge Agent must support foreign, domestic, and local models through a normalized contract while preserving provider-specific capabilities.

## Required Provider Families

### Foreign

- OpenAI / ChatGPT API
- Anthropic / Claude API
- Google / Gemini API
- xAI / Grok API

### Domestic

- DeepSeek
- Alibaba Qwen / DashScope / Model Studio
- Zhipu GLM
- Xiaomi MiMo
- MiniMax
- Volcengine Doubao / Ark

### Local Or Aggregated

- Ollama
- LM Studio
- vLLM
- llama.cpp OpenAI-compatible server
- OpenRouter
- SiliconFlow
- other OpenAI-compatible gateways

## Provider Files

- `01-normalized-provider-contract.md`: internal API and config contract.
- `02-domestic-provider-matrix.md`: DeepSeek, Qwen, GLM, MiMo, MiniMax, Doubao.
- `03-foreign-provider-matrix.md`: OpenAI/ChatGPT, Claude, Gemini, Grok.
- `04-provider-routing-policy.md`: how roles choose models.
- `05-provider-verification-and-acceptance.md`: how to certify a provider profile.
- `06-official-source-notes.md`: official source links and refresh rules.

## Provider Certification Levels

| Level | Meaning |
| --- | --- |
| `profiled` | Config exists and source docs reviewed |
| `shape_tested` | Unit tests verify request and response shape with fake transport |
| `smoke_tested` | Real API call succeeds with user's key |
| `workflow_tested` | Provider completes a fake or demo chapter workflow |
| `certified` | Provider passes capability probe, retry, fallback, and workflow tests |

## Rule

A provider profile must not be called `certified` until its task card passes every acceptance item.
