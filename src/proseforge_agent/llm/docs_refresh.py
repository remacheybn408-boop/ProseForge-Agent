"""Provider documentation refresh source map.

Task 30 turns the provider source notes into an auditable maintenance loop. The
links are intentionally explicit here so certification records can store the
source URLs that informed the current shape check.
"""

from __future__ import annotations

from ..reports import Report, ReportSection


OFFICIAL_SOURCE_URLS: dict[str, list[str]] = {
    "openai": [
        "https://developers.openai.com/api/reference/responses/overview/",
        "https://developers.openai.com/api/docs/guides/migrate-to-responses",
    ],
    "anthropic": [
        "https://platform.claude.com/docs/en/api/messages",
        "https://platform.claude.com/docs/en/api/overview",
    ],
    "gemini": [
        "https://ai.google.dev/gemini-api/docs",
        "https://ai.google.dev/gemini-api/docs/openai",
    ],
    "xai": [
        "https://docs.x.ai/overview",
        "https://docs.x.ai/developers/quickstart",
    ],
    "deepseek": [
        "https://api-docs.deepseek.com/",
        "https://api-docs.deepseek.com/guides/anthropic_api",
    ],
    "qwen": [
        "https://www.alibabacloud.com/help/en/model-studio/compatibility-of-openai-with-dashscope",
        "https://www.alibabacloud.com/help/en/model-studio/qwen-api-reference/",
        "https://www.alibabacloud.com/help/en/model-studio/first-api-call-to-qwen",
    ],
    "glm": [
        "https://docs.bigmodel.cn/cn/guide/develop/openai/introduction",
        "https://docs.bigmodel.cn/cn/guide/develop/others",
        "https://docs.bigmodel.cn/cn/guide/develop/claude/introduction",
    ],
    "mimo": [
        "https://mimo.mi.com/docs/en-US/quick-start/summary/first-api-call",
        "https://mimo.mi.com/docs/en-US/api/chat/openai-api",
        "https://mimo.xiaomi.com/mimocode/models-provider",
    ],
    "minimax": [
        "https://platform.minimax.io/docs/api-reference/text-openai-api",
        "https://platform.minimax.io/docs/api-reference/text-chat-openai",
        "https://platform.minimax.io/docs/api-reference/api-overview",
    ],
    "doubao": [
        "https://www.volcengine.com/docs/82379/1330626",
        "https://www.volcengine.com/docs/82379",
    ],
}


def source_urls_for_family(family: str) -> list[str]:
    """Return official source URLs for a provider family."""
    return list(OFFICIAL_SOURCE_URLS.get(family, []))


def docs_refresh_report(families: list[str]) -> Report:
    """Render a compact docs refresh report for provider families."""
    lines: list[str] = []
    data: dict[str, list[str]] = {}
    for family in families:
        urls = source_urls_for_family(family)
        data[family] = urls
        lines.append(f"{family}: {len(urls)} source URL(s)")
    return Report(
        title="Provider Docs Refresh",
        status="ok",
        next_action="Use these source URLs in provider certification records",
        sections=[ReportSection("Sources", lines)],
        data={"providers": data},
    )


__all__ = ["OFFICIAL_SOURCE_URLS", "source_urls_for_family", "docs_refresh_report"]
