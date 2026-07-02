"""Provider usage metering, budget enforcement, and rate-limit backoff.

``UsageMeter`` records prompt/completion tokens for a provider call and computes
its cost from a static price table (a data table, never a live pricing call).
``BudgetPolicy`` enforces per-run and per-day caps *before* a call spends, so a
blocked step raises :class:`ProviderError` while its prompt pack stays intact and
resumable. ``RateLimitBackoff`` yields increasing, bounded delays so a
rate-limited provider is retried without looping forever.

These wrap provider calls; they never mutate request or response content. Usage
records are UTF-8 JSON with relative paths, so the behaviour is identical on
Windows, macOS, and Linux.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, TypeVar

from ..errors import ConfigurationError, ProviderError

T = TypeVar("T")


@dataclass(frozen=True)
class UsageRecord:
    """Token and cost accounting for a single provider call."""

    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost: float

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "model": self.model,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "cost": round(self.cost, 8),
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "UsageRecord":
        return cls(
            provider=payload["provider"],
            model=payload["model"],
            prompt_tokens=int(payload["prompt_tokens"]),
            completion_tokens=int(payload["completion_tokens"]),
            cost=float(payload["cost"]),
        )


class UsageMeter:
    """Record token usage and compute cost from a static price table.

    The price table is ``{provider: {model: {input_per_1k, output_per_1k}}}``.
    An unknown ``(provider, model)`` is reported as a :class:`ConfigurationError`
    rather than silently billed as free.
    """

    def __init__(self, price_table: dict, records: list[UsageRecord] | None = None):
        self._prices = price_table
        self.records: list[UsageRecord] = list(records) if records else []

    def _price_for(self, provider: str, model: str) -> dict:
        entry = self._prices.get(provider, {}).get(model) if isinstance(self._prices, dict) else None
        if entry is None:
            raise ConfigurationError(
                f"no price entry for provider={provider!r} model={model!r}; "
                "add it to the price table instead of billing it as free"
            )
        return entry

    def cost_for(self, provider: str, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        entry = self._price_for(provider, model)
        return (
            prompt_tokens / 1000.0 * float(entry["input_per_1k"])
            + completion_tokens / 1000.0 * float(entry["output_per_1k"])
        )

    def record(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> UsageRecord:
        cost = self.cost_for(provider, model, prompt_tokens, completion_tokens)
        record = UsageRecord(provider, model, prompt_tokens, completion_tokens, cost)
        self.records.append(record)
        return record

    def total_cost(self) -> float:
        return sum(record.cost for record in self.records)


@dataclass(frozen=True)
class BudgetPolicy:
    """Per-run and per-day spend caps, checked before a call spends."""

    per_run: float | None = None
    per_day: float | None = None

    def check(
        self,
        spent: float,
        day_spent: float | None = None,
        *,
        pending_spend: float = 0.0,
    ) -> None:
        """Raise :class:`ProviderError` if this spend would exceed a cap.

        Called *before* the provider request is sent, so the caller still holds
        the prompt pack and can resume the step once the budget is raised.
        ``spent`` may already include the next call for legacy callers; newer
        callers can pass current spend plus ``pending_spend`` for a clearer
        preflight check.
        """
        projected = spent + pending_spend
        if self.per_run is not None and projected > self.per_run:
            raise ProviderError(
                f"per-run budget exceeded: {projected:.6f} > {self.per_run:.6f}"
            )
        day = day_spent if day_spent is not None else spent
        projected_day = day + pending_spend
        if self.per_day is not None and projected_day > self.per_day:
            raise ProviderError(
                f"per-day budget exceeded: {projected_day:.6f} > {self.per_day:.6f}"
            )


def guarded_call(
    policy: BudgetPolicy,
    spent: float,
    prompt_pack: object,
    call: Callable[[], T],
    day_spent: float | None = None,
    *,
    pending_spend: float = 0.0,
) -> T:
    """Run ``call`` only if ``policy`` permits the spend.

    When the budget blocks the call, ``call`` is never invoked and ``prompt_pack``
    is left untouched so the step is resumable. ``prompt_pack`` is accepted purely
    to make the preservation contract explicit at the call site.
    """
    policy.check(spent, day_spent=day_spent, pending_spend=pending_spend)
    return call()


@dataclass(frozen=True)
class RateLimitBackoff:
    """Increasing, bounded retry delays for rate-limited provider calls."""

    base: float = 0.5
    factor: float = 2.0
    max_delay: float = 30.0
    max_attempts: int = 5

    def next_delay(self, attempt: int) -> float:
        """Return the delay before retry ``attempt`` (0-indexed).

        Delays grow geometrically but are capped at ``max_delay``. Exceeding
        ``max_attempts`` raises :class:`ProviderError` so retries are bounded
        and never loop forever.
        """
        if attempt >= self.max_attempts:
            raise ProviderError(
                f"rate-limit retries exhausted after {self.max_attempts} attempts"
            )
        delay = self.base * (self.factor ** attempt)
        return min(delay, self.max_delay)


class UsageLog:
    """Append-only UTF-8 JSONL log of :class:`UsageRecord` entries."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def append(self, record: UsageRecord) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")

    def load(self) -> list[UsageRecord]:
        if not self.path.exists():
            return []
        records: list[UsageRecord] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            records.append(UsageRecord.from_dict(json.loads(line)))
        return records


def build_usage_report(records: list[UsageRecord]) -> dict:
    """Aggregate records into a per-provider usage report."""
    providers: dict[str, dict] = {}
    for record in records:
        agg = providers.setdefault(
            record.provider,
            {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "cost": 0.0},
        )
        agg["prompt_tokens"] += record.prompt_tokens
        agg["completion_tokens"] += record.completion_tokens
        agg["total_tokens"] += record.total_tokens
        agg["cost"] = round(agg["cost"] + record.cost, 8)
    total_cost = round(sum(record.cost for record in records), 8)
    return {
        "providers": providers,
        "total_cost": total_cost,
        "record_count": len(records),
    }


def render_usage_json(report: dict) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)


def render_usage_markdown(report: dict) -> str:
    lines = ["# Provider Usage Report", ""]
    if not report["providers"]:
        lines.append("No usage recorded.")
        lines.append("")
    else:
        lines.append("| Provider | Prompt | Completion | Cost |")
        lines.append("| --- | ---: | ---: | ---: |")
        for provider in sorted(report["providers"]):
            agg = report["providers"][provider]
            lines.append(
                f"| {provider} | {agg['prompt_tokens']} | "
                f"{agg['completion_tokens']} | {agg['cost']:.6f} |"
            )
        lines.append("")
    lines.append(f"**Total cost:** {report['total_cost']:.6f}")
    lines.append(f"**Records:** {report['record_count']}")
    return "\n".join(lines)


__all__ = [
    "UsageRecord",
    "UsageMeter",
    "BudgetPolicy",
    "guarded_call",
    "RateLimitBackoff",
    "UsageLog",
    "build_usage_report",
    "render_usage_json",
    "render_usage_markdown",
]
