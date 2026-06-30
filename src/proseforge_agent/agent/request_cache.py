"""Deterministic request cache for provider calls."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RequestCacheKey:
    """Stable cache key derived from provider request inputs."""

    value: str
    prompt_hash: str
    system_prompt_version: str
    provider: str
    model: str
    evidence_hash: str
    tool_result_hash: str
    temperature: float

    @classmethod
    def build(
        cls,
        *,
        prompt: str,
        system_prompt_version: str,
        provider: str,
        model: str,
        evidence: list[Any],
        tool_results: list[Any],
        temperature: float,
    ) -> "RequestCacheKey":
        prompt_hash = _hash(prompt)
        evidence_hash = _hash_json(evidence)
        tool_result_hash = _hash_json(tool_results)
        payload = {
            "prompt_hash": prompt_hash,
            "system_prompt_version": system_prompt_version,
            "provider": provider,
            "model": model,
            "evidence_hash": evidence_hash,
            "tool_result_hash": tool_result_hash,
            "temperature": temperature,
        }
        return cls(
            value=f"reqcache_{_hash_json(payload)}",
            prompt_hash=prompt_hash,
            system_prompt_version=system_prompt_version,
            provider=provider,
            model=model,
            evidence_hash=evidence_hash,
            tool_result_hash=tool_result_hash,
            temperature=temperature,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RequestCacheKey":
        return cls(
            value=str(payload["value"]),
            prompt_hash=str(payload["prompt_hash"]),
            system_prompt_version=str(payload["system_prompt_version"]),
            provider=str(payload["provider"]),
            model=str(payload["model"]),
            evidence_hash=str(payload["evidence_hash"]),
            tool_result_hash=str(payload["tool_result_hash"]),
            temperature=float(payload["temperature"]),
        )


@dataclass(frozen=True)
class CachedResponse:
    """Cached provider response payload."""

    key: RequestCacheKey
    payload: dict[str, Any]
    cache_hit: bool
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key.to_dict(),
            "payload": self.payload,
            "cache_hit": self.cache_hit,
            "created_at": self.created_at,
        }


class RequestCache:
    """JSON-backed request cache."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.path = self.root / "cache" / "requests.json"

    def put(self, key: RequestCacheKey, payload: dict[str, Any]) -> CachedResponse:
        cache = self._read()
        created_at = datetime.now(UTC).isoformat()
        cache[key.value] = {
            "key": key.to_dict(),
            "payload": payload,
            "created_at": created_at,
        }
        self._write(cache)
        return CachedResponse(key=key, payload=payload, cache_hit=False, created_at=created_at)

    def get(
        self,
        key: RequestCacheKey,
        *,
        audit_store: Any | None = None,
        session_id: str = "cache",
    ) -> CachedResponse | None:
        payload = self._read().get(key.value)
        if payload is None:
            return None
        response = CachedResponse(
            key=RequestCacheKey.from_dict(payload["key"]),
            payload=dict(payload.get("payload") or {}),
            cache_hit=True,
            created_at=str(payload.get("created_at", "")),
        )
        if audit_store is not None:
            audit_store.record_turn(
                session_id,
                {
                    "input": key.value,
                    "intent": {"name": "cache_lookup"},
                    "system_prompt_version": key.system_prompt_version,
                    "provider": {"name": key.provider, "model": key.model},
                    "model_output": f"cache hit: {key.value}",
                    "final_action": "cache_hit",
                },
            )
        return response

    def list(self) -> list[CachedResponse]:
        entries = []
        for payload in self._read().values():
            entries.append(
                CachedResponse(
                    key=RequestCacheKey.from_dict(payload["key"]),
                    payload=dict(payload.get("payload") or {}),
                    cache_hit=False,
                    created_at=str(payload.get("created_at", "")),
                )
            )
        return sorted(entries, key=lambda item: item.key.value)

    def stats(self) -> dict[str, Any]:
        entries = self.list()
        return {"entries": len(entries), "keys": [entry.key.value for entry in entries]}

    def clear(self) -> int:
        count = len(self._read())
        self._write({})
        return count

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, cache: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _hash_json(value: Any) -> str:
    return _hash(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


__all__ = ["CachedResponse", "RequestCache", "RequestCacheKey"]
