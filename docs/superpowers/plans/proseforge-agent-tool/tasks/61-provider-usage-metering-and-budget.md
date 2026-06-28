# Task 61: Provider Usage Metering And Budget

## Goal

Meter token usage and cost per provider call, enforce budgets, and back off on rate limits.

## Agent Product Requirement

A multi-provider agent that calls paid APIs must let users see and cap spending, and must survive rate limits without losing work.

> Dependency note: execute after the provider layer (Tasks 04–06). Logical position: 06.5.

## Architecture Notes

`llm.usage` wraps every provider call to record prompt/completion tokens and computed cost, enforce a per-run and per-day budget, and apply rate-limit backoff. It sits inside the provider gateway so workflow and chat get metering for free; it does not change provider adapter shapes. Cost comes from a static price table per model. When a budget is exceeded it raises `ProviderError` before the call, preserving the prompt pack so the step can resume later (consistent with the Provider call error boundary in architecture 02).

Read before starting:

- ../architecture/02-system-architecture.md (Error Boundaries)
- ../architecture/05-model-provider-adapters.md
- 00-task-index.md

## Files

- Create `src/proseforge_agent/llm/usage.py`
- Create `tests/test_provider_usage_metering.py`
- Create `tests/fixtures/provider-usage-metering-and-budget/price_table.json`

## Interfaces / Contracts

- `UsageMeter(price_table).record(provider, model, prompt_tokens, completion_tokens) -> UsageRecord` with computed `cost`.
- `BudgetPolicy(per_run, per_day).check(spent) -> None` raises `ProviderError` when a cap would be exceeded.
- `RateLimitBackoff.next_delay(attempt) -> float` returns increasing delays; retries are bounded.
- Metering wraps the call; it never mutates request/response content.

## Data Flow

1. Before a provider call, check the budget against spend-so-far.
2. Execute the call through the existing gateway.
3. Record prompt/completion tokens and compute cost from the price table.
4. On a rate-limit response, back off and retry within the bound.
5. Persist the usage record and return it with the result.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_provider_usage_metering.py::test_meter_records_tokens_and_computes_cost`**

```python
def test_meter_records_tokens_and_computes_cost(price_table):
    meter = UsageMeter(price_table)
    record = meter.record(provider="deepseek", model="deepseek-chat",
                          prompt_tokens=1000, completion_tokens=500)
    assert record.prompt_tokens == 1000
    assert record.completion_tokens == 500
    assert record.cost > 0
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/test_provider_usage_metering.py::test_meter_records_tokens_and_computes_cost -q
```

Expected: FAIL because `UsageMeter` and `UsageRecord` are missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement `UsageMeter`, `UsageRecord`, `BudgetPolicy`, and `RateLimitBackoff`.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/test_provider_usage_metering.py::test_meter_records_tokens_and_computes_cost -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

```text
test_budget_exceeded_raises_provider_error_before_call
test_prompt_pack_is_preserved_when_budget_blocks_a_call
test_rate_limit_backoff_delays_increase_and_are_bounded
test_unknown_model_in_price_table_is_reported_not_silently_zero
test_usage_report_renders_markdown_and_json
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_provider_usage_metering.py -q
pf-agent usage report --since today
```

Expected: tests pass and the usage report shows per-provider tokens and cost.

- [ ] **Step 7: Record commit boundary**

```powershell
git add src/proseforge_agent/llm/usage.py tests/test_provider_usage_metering.py tests/fixtures/provider-usage-metering-and-budget
git commit -m "feat: add provider usage metering and budget"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Cross-Platform Notes

- Usage records are UTF-8 JSON with relative paths.
- Cost is computed from a data table, not a live pricing call.
- Works identically on Windows, macOS, and Linux.

## Failure Modes To Prove

- A budget-exceeding call raises `ProviderError` before spending, preserving the prompt pack.
- Rate-limit backoff is bounded; it does not retry forever.
- An unknown model in the price table is reported, not silently treated as free.
- Metering never alters request or response content.

## Verification

```powershell
python -m pytest tests/test_provider_usage_metering.py -q
pf-agent usage report --since today
```

## Acceptance

- Every provider call records tokens and cost.
- Per-run and per-day budgets are enforced.
- Rate limits trigger bounded backoff, not data loss.
- Usage is reportable as Markdown and JSON.

## Commit Boundary

Commit only usage/metering files and tests after verification passes. Do not change provider adapter shapes here.
