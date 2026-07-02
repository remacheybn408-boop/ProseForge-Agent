"""Tests for provider usage metering and budget (Task 61)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from proseforge_agent.errors import ConfigurationError, ProviderError
from proseforge_agent.llm.usage import (
    BudgetPolicy,
    RateLimitBackoff,
    UsageLog,
    UsageMeter,
    UsageRecord,
    build_usage_report,
    guarded_call,
    render_usage_json,
    render_usage_markdown,
)

FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "provider-usage-metering-and-budget"
    / "price_table.json"
)


@pytest.fixture
def price_table() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_meter_records_tokens_and_computes_cost(price_table):
    meter = UsageMeter(price_table)
    record = meter.record(
        provider="deepseek",
        model="deepseek-chat",
        prompt_tokens=1000,
        completion_tokens=500,
    )
    assert record.prompt_tokens == 1000
    assert record.completion_tokens == 500
    assert record.cost > 0
    # 1000/1000*0.00014 + 500/1000*0.00028 = 0.00014 + 0.00014 = 0.00028
    assert record.cost == pytest.approx(0.00028)


def test_budget_exceeded_raises_provider_error_before_call(price_table):
    policy = BudgetPolicy(per_run=0.01)
    with pytest.raises(ProviderError):
        policy.check(spent=0.02)


def test_prompt_pack_is_preserved_when_budget_blocks_a_call():
    policy = BudgetPolicy(per_run=0.01)
    prompt_pack = {"messages": [{"role": "user", "content": "讲个开头"}]}
    original = json.loads(json.dumps(prompt_pack))
    calls: list[str] = []

    def call():
        calls.append("ran")
        return "result"

    with pytest.raises(ProviderError):
        guarded_call(policy, spent=0.5, prompt_pack=prompt_pack, call=call)

    # The blocked call never spent, and the prompt pack is untouched so the
    # step can resume later.
    assert calls == []
    assert prompt_pack == original


def test_pending_spend_blocks_budget_before_call():
    policy = BudgetPolicy(per_run=0.01)
    with pytest.raises(ProviderError):
        policy.check(spent=0.009, pending_spend=0.002)


def test_guarded_call_pending_spend_blocks_without_calling_provider():
    policy = BudgetPolicy(per_run=0.01)
    calls: list[str] = []

    def call():
        calls.append("ran")
        return "result"

    with pytest.raises(ProviderError):
        guarded_call(policy, spent=0.009, pending_spend=0.002, prompt_pack={}, call=call)

    assert calls == []


def test_rate_limit_backoff_delays_increase_and_are_bounded():
    backoff = RateLimitBackoff(base=0.5, factor=2.0, max_delay=8.0, max_attempts=5)
    delays = [backoff.next_delay(i) for i in range(5)]
    assert delays == sorted(delays)
    assert delays == [0.5, 1.0, 2.0, 4.0, 8.0]
    assert all(d <= 8.0 for d in delays)
    # Bounded: it does not retry forever.
    with pytest.raises(ProviderError):
        backoff.next_delay(5)


def test_unknown_model_in_price_table_is_reported_not_silently_zero(price_table):
    meter = UsageMeter(price_table)
    with pytest.raises(ConfigurationError):
        meter.record(
            provider="deepseek",
            model="deepseek-unknown",
            prompt_tokens=10,
            completion_tokens=10,
        )


def test_usage_report_renders_markdown_and_json(price_table):
    meter = UsageMeter(price_table)
    meter.record("deepseek", "deepseek-chat", 1000, 500)
    meter.record("openai", "gpt-4o", 200, 100)
    report = build_usage_report(meter.records)

    assert report["providers"]["deepseek"]["prompt_tokens"] == 1000
    assert report["providers"]["openai"]["completion_tokens"] == 100
    assert report["total_cost"] > 0

    markdown = render_usage_markdown(report)
    assert "deepseek" in markdown
    assert "openai" in markdown

    parsed = json.loads(render_usage_json(report))
    assert parsed["total_cost"] == report["total_cost"]


def test_usage_log_round_trips_records(tmp_path):
    log_path = tmp_path / "usage.jsonl"
    log = UsageLog(log_path)
    log.append(UsageRecord("deepseek", "deepseek-chat", 1000, 500, 0.00028))
    log.append(UsageRecord("openai", "gpt-4o", 200, 100, 0.0015))

    loaded = UsageLog(log_path).load()
    assert len(loaded) == 2
    assert loaded[0].provider == "deepseek"
    assert loaded[1].model == "gpt-4o"
