# Phase 02: Full Model Provider Adaptation

Dates: 2026-07-06 to 2026-07-19.

Goal: make ChatGPT, Claude, Gemini, Grok, DeepSeek, Qwen, GLM, MiMo, MiniMax, and Doubao first-class provider targets with certification gates.

## Day 11: 2026-07-06, OpenAI / ChatGPT Provider

Primary objective: implement and certify the OpenAI provider profile.

Context to read:

- `tasks/18-provider-openai-chatgpt.md`
- `providers/03-foreign-provider-matrix.md`
- OpenAI API documentation.

Work blocks:

- Morning: create OpenAI profile with base URL, key environment variable, model configuration, streaming support, tools support, structured output support, and embedding support flags.
- Midday: add fake transport tests for chat generation, stream events, tool calls, structured JSON request mode, refusal or safety metadata, and usage parsing.
- Afternoon: add CLI smoke command that can run offline shape test and optional real-key smoke test.
- Closeout: write certification record.

Expected outputs:

- OpenAI provider profile.
- OpenAI tests.
- Certification record.

Verification:

```powershell
python -m pytest -q tests
pf-agent provider certify --provider openai --shape-only
```

Acceptance checklist:

- The provider can be selected by role: planner, drafter, critic, reviser, memory, embedding.
- Missing `OPENAI_API_KEY` yields a clear skip message for real smoke tests.
- Offline shape tests pass.
- The profile records supported and unsupported capabilities explicitly.

Stop condition:

- Stop when OpenAI can be used without changing core workflow code.

## Day 12: 2026-07-07, Anthropic / Claude Provider

Primary objective: implement native Anthropic Claude support.

Context to read:

- `tasks/19-provider-anthropic-claude.md`
- `providers/03-foreign-provider-matrix.md`
- Anthropic Messages API documentation.

Work blocks:

- Morning: implement Anthropic request adapter for system messages, user messages, assistant prefill, max tokens, temperature, tools, and streaming events.
- Midday: implement response parser for content blocks, tool-use blocks, stop reasons, usage, and error body mapping.
- Afternoon: add fake transport tests for normal content, tool use, stream deltas, rate limit, authentication failure, and overloaded response.
- Closeout: update provider certification record.

Expected outputs:

- Anthropic native provider profile.
- Request and response mappers.
- Tests and certification record.

Verification:

```powershell
python -m pytest -q tests
pf-agent provider certify --provider anthropic --shape-only
```

Acceptance checklist:

- Claude can be used as critic and reviser without losing system instruction semantics.
- Tool-call shapes are normalized into the common provider contract.
- Streaming content blocks become normalized stream events.
- Real smoke test is optional and clearly gated by `ANTHROPIC_API_KEY`.

Stop condition:

- Stop when Claude is a native provider rather than a compatible-endpoint guess.

## Day 13: 2026-07-08, Google / Gemini Provider

Primary objective: implement Gemini provider support with native and OpenAI-compatible routes where useful.

Context to read:

- `tasks/20-provider-google-gemini.md`
- `providers/03-foreign-provider-matrix.md`
- Google Gemini API documentation.

Work blocks:

- Morning: create Gemini profile with native endpoint metadata and OpenAI-compatible endpoint metadata.
- Midday: implement request mapper for content parts, system instructions, tools, generation config, safety settings, and streaming.
- Afternoon: add tests for text, JSON-like output, tool calls, stream chunks, safety block response, and usage metadata.
- Closeout: record when the profile should use native mode versus compatible mode.

Expected outputs:

- Gemini provider profile.
- Gemini request and response tests.
- Mode-selection rule.

Verification:

```powershell
python -m pytest -q tests
pf-agent provider certify --provider gemini --shape-only
```

Acceptance checklist:

- Gemini can be selected for planner, drafter, critic, and multimodal future roles.
- Native safety responses are mapped into normalized provider statuses.
- Compatible mode is tested as transport shape, not assumed to cover all native features.
- Missing `GEMINI_API_KEY` does not fail offline tests.

Stop condition:

- Stop when Gemini support has a clear native path and a compatible fallback path.

## Day 14: 2026-07-09, xAI / Grok Provider

Primary objective: implement Grok provider profile through xAI's OpenAI-compatible API shape.

Context to read:

- `tasks/21-provider-xai-grok.md`
- `providers/03-foreign-provider-matrix.md`
- xAI API documentation.

Work blocks:

- Morning: add Grok provider profile with base URL, key environment variable, model configuration, stream support, and tool support flags.
- Midday: reuse OpenAI-compatible transport and add xAI-specific error mapping tests.
- Afternoon: add certification command output for Grok roles and limits.
- Closeout: document when Grok is recommended for brainstorming, dialogue variation, or market-tone comparison.

Expected outputs:

- Grok provider profile.
- Shape tests.
- Certification record.

Verification:

```powershell
python -m pytest -q tests
pf-agent provider certify --provider grok --shape-only
```

Acceptance checklist:

- Grok uses the shared compatible transport without special-case leakage.
- Error mapping covers authentication, rate limit, and server errors.
- Role recommendations are documented but not hard-coded into the provider itself.
- Missing `XAI_API_KEY` only skips real smoke tests.

Stop condition:

- Stop when all foreign requested providers have explicit profiles.

## Day 15: 2026-07-10, DeepSeek Provider

Primary objective: implement DeepSeek provider profile and reasoning-aware metadata.

Context to read:

- `tasks/22-provider-deepseek.md`
- `providers/02-domestic-provider-matrix.md`
- DeepSeek API documentation.

Work blocks:

- Morning: create DeepSeek profile with base URL, key variable, model configuration, compatible transport, streaming support, and reasoning-output handling flags.
- Midday: add tests for normal text, stream, model override, usage parsing, rate limit, and reasoning metadata preservation when the API returns it.
- Afternoon: add role recommendation for planner, outline critic, logic checker, and code-assistant support.
- Closeout: write certification record.

Expected outputs:

- DeepSeek provider profile.
- Tests and role metadata.
- Certification record.

Verification:

```powershell
python -m pytest -q tests
pf-agent provider certify --provider deepseek --shape-only
```

Acceptance checklist:

- DeepSeek can run through compatible transport.
- Reasoning-like fields are preserved in raw metadata while final workflow prompts avoid exposing private chain-of-thought.
- Profile model is configurable by environment or config file.
- Missing `DEEPSEEK_API_KEY` is a clean skip for real smoke.

Stop condition:

- Stop when DeepSeek is certified as a domestic first-class provider.

## Day 16: 2026-07-11, Qwen / DashScope Provider

Primary objective: implement Alibaba Qwen through DashScope compatible mode and record native expansion hooks.

Context to read:

- `tasks/23-provider-qwen-dashscope.md`
- `providers/02-domestic-provider-matrix.md`
- Alibaba Cloud Model Studio or DashScope documentation.

Work blocks:

- Morning: create Qwen profile with DashScope compatible base URL, key variable, model configuration, stream flag, tools flag, and embedding flag.
- Midday: add tests for compatible request shape, stream parse, tool-call parse, error mapping, and DashScope-specific headers.
- Afternoon: define native DashScope extension hook for later multimodal or agent-specific APIs.
- Closeout: update certification record.

Expected outputs:

- Qwen provider profile.
- DashScope compatible tests.
- Native expansion notes.

Verification:

```powershell
python -m pytest -q tests
pf-agent provider certify --provider qwen --shape-only
```

Acceptance checklist:

- Qwen can be used as drafter, reviser, critic, and embedding provider when configured.
- Compatible-mode behavior is tested without a real API call.
- Native expansion point is documented in provider metadata.
- Missing `DASHSCOPE_API_KEY` only affects real smoke tests.

Stop condition:

- Stop when Qwen is usable through the same workflow roles as foreign providers.

## Day 17: 2026-07-12, Zhipu GLM Provider

Primary objective: implement GLM provider profile for Zhipu BigModel and Z.ai coding endpoint separation.

Context to read:

- `tasks/24-provider-zhipu-glm.md`
- `providers/02-domestic-provider-matrix.md`
- Zhipu BigModel documentation.

Work blocks:

- Morning: create GLM profile with BigModel base URL, key variable, model configuration, compatible transport, and tool support flags.
- Midday: create optional Z.ai coding-plan profile as a separate provider route, not a hidden mode inside GLM.
- Afternoon: add tests for both route shapes, headers, error mapping, and capability separation.
- Closeout: record certification status for GLM writing roles and Z.ai coding-assistant role.

Expected outputs:

- GLM provider profile.
- Optional Z.ai coding provider profile.
- Tests and certification records.

Verification:

```powershell
python -m pytest -q tests
pf-agent provider certify --provider glm --shape-only
```

Acceptance checklist:

- GLM writing profile and coding-plan profile are not conflated.
- Config names make the route clear to operators.
- Shape tests pass without keys.
- Missing `ZHIPU_API_KEY` and `ZAI_API_KEY` are handled independently.

Stop condition:

- Stop when GLM support is clear for fiction work and coding-support work.

## Day 18: 2026-07-13, Xiaomi MiMo Provider

Primary objective: implement MiMo provider as a configurable profile that can follow official endpoint updates.

Context to read:

- `tasks/25-provider-xiaomi-mimo.md`
- `providers/02-domestic-provider-matrix.md`
- Xiaomi MiMo official materials available at implementation time.

Work blocks:

- Morning: create MiMo profile using configurable base URL, key variable, model configuration, and compatibility mode.
- Midday: add strict config validation so the profile cannot run real smoke tests without confirmed base URL and model.
- Afternoon: add shape tests for request construction, response parsing, streaming if supported, and error mapping.
- Closeout: write certification record with "shape certified" and "real endpoint certification required before production use" status.

Expected outputs:

- MiMo configurable provider profile.
- Config validation tests.
- Certification record.

Verification:

```powershell
python -m pytest -q tests
pf-agent provider certify --provider mimo --shape-only
```

Acceptance checklist:

- MiMo is included as a first-class provider family.
- Unconfirmed endpoint details are not hard-coded.
- Operators receive exact config fields needed for real certification.
- The fallback router can choose MiMo once capability probing succeeds.

Stop condition:

- Stop when MiMo has a safe, certifiable adapter path.

## Day 19: 2026-07-14, MiniMax Provider

Primary objective: implement MiniMax provider profile for writing and coding-capable roles.

Context to read:

- `tasks/26-provider-minimax.md`
- `providers/02-domestic-provider-matrix.md`
- MiniMax platform documentation.

Work blocks:

- Morning: create MiniMax profile with base URL, key variable, model configuration, compatible transport, and long-context capability fields.
- Midday: add tests for request shape, stream shape, usage parse, error mapping, and long-context metadata.
- Afternoon: define recommended roles: drafting, polishing, dialogue variation, and code-assistant where certified.
- Closeout: write certification record.

Expected outputs:

- MiniMax provider profile.
- Tests and role metadata.
- Certification record.

Verification:

```powershell
python -m pytest -q tests
pf-agent provider certify --provider minimax --shape-only
```

Acceptance checklist:

- MiniMax can be routed by provider role.
- Long-context claim is stored as configurable metadata and verified during real smoke.
- Missing `MINIMAX_API_KEY` skips real smoke cleanly.
- Provider-specific response details stay inside adapter layer.

Stop condition:

- Stop when MiniMax is ready for capability probing.

## Day 20: 2026-07-15, Doubao / Volcengine Ark Provider

Primary objective: implement Doubao provider through Volcengine Ark.

Context to read:

- `tasks/27-provider-volcengine-doubao.md`
- `providers/02-domestic-provider-matrix.md`
- Volcengine Ark documentation.

Work blocks:

- Morning: create Doubao profile with Ark base URL, key variable, endpoint or model configuration, compatible transport, and regional configuration.
- Midday: add tests for Ark request shape, stream parse, endpoint-id model configuration, region field handling, and error mapping.
- Afternoon: document recommended roles: drafting, Chinese market style critique, rewrite, and cost-balanced fallback.
- Closeout: write certification record.

Expected outputs:

- Doubao provider profile.
- Ark-specific tests.
- Certification record.

Verification:

```powershell
python -m pytest -q tests
pf-agent provider certify --provider doubao --shape-only
```

Acceptance checklist:

- Doubao is configured through Ark without hard-coding private endpoint IDs.
- Region and endpoint settings are explicit.
- Shape tests pass offline.
- Missing `ARK_API_KEY` only skips real smoke.

Stop condition:

- Stop when every requested domestic provider has a profile.

## Day 21: 2026-07-16, Capability Probing

Primary objective: detect provider capabilities automatically instead of trusting static labels.

Context to read:

- `tasks/28-provider-capability-probing.md`
- `providers/05-provider-verification-and-acceptance.md`

Work blocks:

- Morning: define probing prompts for text generation, streaming, JSON output, tool calls, long context, embedding, safety behavior, and retry behavior.
- Midday: implement offline probe replay and optional real probe mode.
- Afternoon: store probe results with timestamp, provider, model, endpoint, success status, latency, usage, and observed capabilities.
- Closeout: add report command for capability matrix.

Expected outputs:

- Capability probing module.
- Probe result schema.
- Provider capability report.

Verification:

```powershell
python -m pytest -q tests
pf-agent provider probe --provider fake --write-report
```

Acceptance checklist:

- Capability flags can be confirmed or rejected by probes.
- Real probes never run unless explicitly requested.
- Probe reports are human-readable and machine-readable.
- Provider routing can consume probe results.

Stop condition:

- Stop when routing no longer depends only on static provider promises.

## Day 22: 2026-07-17, Fallback Router

Primary objective: route novel-writing roles across providers by capability, cost, locality, latency, and reliability.

Context to read:

- `tasks/29-provider-fallback-router.md`
- `providers/04-provider-routing-policy.md`

Work blocks:

- Morning: implement route policy for planner, drafter, critic, reviser, memory, embedding, market analyst, and code assistant roles.
- Midday: add fallback chains for domestic-only mode, foreign-only mode, privacy-strict mode, low-cost mode, and high-quality mode.
- Afternoon: add tests for unavailable provider, missing key, failed probe, retryable error, non-retryable error, and manual override.
- Closeout: generate sample route report.

Expected outputs:

- Provider router.
- Routing policy tests.
- Route report command.

Verification:

```powershell
python -m pytest -q tests
pf-agent provider routes --config configs/agent.example.yaml
```

Acceptance checklist:

- The router can choose from all requested model families.
- Domestic and foreign providers can be isolated by policy.
- Fallback decisions explain why a provider was selected or skipped.
- Retry rules respect idempotency and workflow state.

Stop condition:

- Stop when the agent can survive a provider outage without losing workflow state.

## Day 23: 2026-07-18, Provider Docs Refresh And Certification

Primary objective: create repeatable docs-refresh and certification practice for unstable provider APIs.

Context to read:

- `tasks/30-provider-docs-refresh-and-certification.md`
- `providers/06-official-source-notes.md`

Work blocks:

- Morning: implement docs-refresh checklist that records official doc URL, checked date, base URL, auth method, model naming rule, streaming support, tools support, and known incompatibilities.
- Midday: implement provider certification file format and CLI output.
- Afternoon: run shape certification for all providers.
- Closeout: create a provider certification summary.

Expected outputs:

- Docs-refresh checklist.
- Certification record format.
- Certification summary.

Verification:

```powershell
python -m pytest -q tests
pf-agent provider certify --all --shape-only --write-report
```

Acceptance checklist:

- Every provider has a certification record.
- Each record has a source URL and checked date.
- Shape certification can run without API keys.
- Real certification is separated from shape certification.

Stop condition:

- Stop when provider maintenance is an explicit workflow, not tribal knowledge.

## Day 24: 2026-07-19, Phase 02 Integration Gate

Primary objective: verify complete provider coverage before memory work begins.

Context to read:

- All Phase 02 task cards.
- Provider certification summary.

Work blocks:

- Morning: run full provider test suite and shape certification.
- Midday: inspect route reports for each role and each policy mode.
- Afternoon: fix provider registry, metadata, or routing mismatches.
- Closeout: write Phase 02 closeout report with gaps, real-key certification status, and memory-phase start context.

Expected outputs:

- Passing provider tests.
- Provider route matrix.
- Phase 02 closeout report.

Verification:

```powershell
python -m pytest -q
pf-agent provider certify --all --shape-only --write-report
pf-agent provider routes --all-policies
```

Acceptance checklist:

- OpenAI, Claude, Gemini, Grok, DeepSeek, Qwen, GLM, MiMo, MiniMax, and Doubao are all represented.
- Each provider has config, tests, capability metadata, and certification status.
- The router can explain provider choices.
- Memory phase can request embeddings or retrieval models through provider roles.

Stop condition:

- Stop when provider work is complete enough for the rest of the product to treat models as interchangeable capabilities.
