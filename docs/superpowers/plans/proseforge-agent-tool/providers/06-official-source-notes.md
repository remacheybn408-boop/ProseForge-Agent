# Official Source Notes

Checked date: 2026-06-26.

Purpose: provider APIs change. These links define where implementers refresh base URLs, authentication rules, model names, protocol support, streaming support, and tool support before real-provider certification.

## Agent Design References

| Source | Link | Used For |
| --- | --- | --- |
| OpenAI Codex Agent Skills | <https://developers.openai.com/codex/skills> | Skill packaging, reusable workflow instructions, resources, and scripts. |
| OpenAI API Skills guide | <https://developers.openai.com/api/docs/guides/tools-skills> | Versioned skill-bundle concept and agent-process modularity. |
| Claude Code Skills docs | <https://code.claude.com/docs/en/skills> | Skill and command separation for operator-facing and agent-facing workflows. |
| Hermes Agent architecture | <https://hermes-agent.nousresearch.com/docs/developer-guide/architecture> | Persistent agent loop, subsystem boundaries, memory and tool architecture. |

## Foreign Provider Sources

| Provider | Link | Refresh Items |
| --- | --- | --- |
| OpenAI / ChatGPT | <https://developers.openai.com/api/reference/responses/overview/> | Responses API shape, tools, output parsing, model naming, usage fields. |
| OpenAI migration guidance | <https://developers.openai.com/api/docs/guides/migrate-to-responses> | When to prefer Responses over Chat Completions for new workflows. |
| Anthropic / Claude | <https://platform.claude.com/docs/en/api/messages> | Messages request shape, content blocks, tools, streaming, usage fields. |
| Anthropic API overview | <https://platform.claude.com/docs/en/api/overview> | SDK behavior, headers, retries, timeouts. |
| Google / Gemini | <https://ai.google.dev/gemini-api/docs> | Native Gemini generate-content behavior, tools, safety, structured output. |
| Gemini OpenAI compatibility | <https://ai.google.dev/gemini-api/docs/openai> | Compatible base URL, supported compatibility features, limitations. |
| xAI / Grok | <https://docs.x.ai/overview> | Responses API style, base URL, model examples, output parsing. |
| xAI quickstart | <https://docs.x.ai/developers/quickstart> | Account, API key, first call, environment setup. |

## Domestic Provider Sources

| Provider | Link | Refresh Items |
| --- | --- | --- |
| DeepSeek | <https://api-docs.deepseek.com/> | OpenAI-compatible base URL, model list, auth, streaming, tool support. |
| DeepSeek Anthropic compatibility | <https://api-docs.deepseek.com/guides/anthropic_api> | Anthropic-compatible endpoint and protocol notes. |
| Qwen / Alibaba Model Studio | <https://www.alibabacloud.com/help/en/model-studio/compatibility-of-openai-with-dashscope> | OpenAI-compatible Chat endpoint, base URL, models, auth. |
| Qwen text generation | <https://www.alibabacloud.com/help/en/model-studio/qwen-api-reference/> | Chat, Responses, DashScope native, built-in tools, model behavior. |
| Qwen first call | <https://www.alibabacloud.com/help/en/model-studio/first-api-call-to-qwen> | API key and first-call setup. |
| Zhipu GLM OpenAI compatibility | <https://docs.bigmodel.cn/cn/guide/develop/openai/introduction> | OpenAI-compatible protocol, differences, base URL. |
| Zhipu GLM Coding Plan tools | <https://docs.bigmodel.cn/cn/guide/develop/others> | Coding-plan OpenAI-compatible base URL and model setup. |
| Zhipu Claude compatibility | <https://docs.bigmodel.cn/cn/guide/develop/claude/introduction> | Anthropic-compatible route for GLM where applicable. |
| Xiaomi MiMo first call | <https://mimo.mi.com/docs/en-US/quick-start/summary/first-api-call> | OpenAI and Anthropic compatibility, key setup, first call. |
| Xiaomi MiMo OpenAI API | <https://mimo.mi.com/docs/en-US/api/chat/openai-api> | Chat Completions compatibility details. |
| Xiaomi MiMo model provider | <https://mimo.xiaomi.com/mimocode/models-provider> | MiMo Platform provider settings, authentication header, model naming. |
| MiniMax OpenAI API | <https://platform.minimax.io/docs/api-reference/text-openai-api> | OpenAI-compatible usage and multimodal input notes. |
| MiniMax Chat Completions | <https://platform.minimax.io/docs/api-reference/text-chat-openai> | `/v1/chat/completions`, MiniMax-M3 capabilities, thinking parameters. |
| MiniMax API overview | <https://platform.minimax.io/docs/api-reference/api-overview> | OpenAI-compatible and Anthropic-compatible API families. |
| Volcengine Ark OpenAI compatibility | <https://www.volcengine.com/docs/82379/1330626> | Ark OpenAI-compatible setup, base URL, model and key configuration. |
| Volcengine Ark docs root | <https://www.volcengine.com/docs/82379> | Ark model service docs, endpoint management, model IDs. |

## Refresh Rule

- Refresh these links before implementing Task 30 and before any release sign-off.
- Record exact checked date, observed base URL, model name used for smoke testing, and unsupported features.
- If a provider's official docs conflict with this plan, update the provider profile and certification record rather than bending the adapter to stale notes.
