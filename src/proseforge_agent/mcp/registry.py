"""Persistent MCP server registry."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any

from ..errors import ConfigurationError
from .client import MCPServerSpec


@dataclass(frozen=True)
class MCPServerConfig:
    """Persistent MCP server configuration."""

    id: str
    display_name: str = ""
    transport: str = "stdio"
    command: list[str] | None = None
    url: str = ""
    env: dict[str, str] | None = None
    env_allow: list[str] = field(default_factory=list)
    secret_refs: dict[str, str] = field(default_factory=dict)
    cwd: str = ""
    enabled: bool = True
    trust_level: str = "local"
    permission_profile: str = "read_only"
    timeout_ms: int = 10000
    rate_limit_per_minute: int = 60

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["command"] = list(self.command or [])
        payload["env"] = dict(self.env or {})
        payload["env_allow"] = list(self.env_allow or [])
        payload["secret_refs"] = dict(self.secret_refs or {})
        return payload

    def to_spec(self) -> MCPServerSpec:
        return MCPServerSpec(
            id=self.id,
            transport=self.transport,
            command=list(self.command or []),
            url=self.url,
            cwd=self.cwd,
            env=dict(self.env or {}),
        )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "MCPServerConfig":
        return cls(
            id=str(payload["id"]),
            display_name=str(payload.get("display_name") or payload["id"]),
            transport=str(payload.get("transport") or "stdio"),
            command=list(payload.get("command") or []),
            url=str(payload.get("url") or ""),
            env={str(key): str(value) for key, value in dict(payload.get("env") or {}).items()},
            env_allow=[str(item) for item in list(payload.get("env_allow") or [])],
            secret_refs={str(key): str(value) for key, value in dict(payload.get("secret_refs") or {}).items()},
            cwd=str(payload.get("cwd") or ""),
            enabled=bool(payload.get("enabled", True)),
            trust_level=str(payload.get("trust_level") or "local"),
            permission_profile=str(payload.get("permission_profile") or "read_only"),
            timeout_ms=int(payload.get("timeout_ms") or 10000),
            rate_limit_per_minute=int(payload.get("rate_limit_per_minute") or 60),
        )


class MCPServerRegistry:
    """Load, save, and mutate MCP server configuration."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.path = self.root / "mcp" / "servers.json"

    def list(self, *, include_disabled: bool = True) -> list[MCPServerConfig]:
        configs = [MCPServerConfig.from_dict(item) for item in self._read().get("servers", [])]
        configs = sorted(configs, key=lambda item: item.id)
        if include_disabled:
            return configs
        return [config for config in configs if config.enabled]

    def get(self, server_id: str) -> MCPServerConfig:
        for config in self.list():
            if config.id == server_id:
                return config
        raise ConfigurationError(f"unknown MCP server {server_id!r}")

    def add(self, config: MCPServerConfig) -> MCPServerConfig:
        configs = self.list()
        if any(existing.id == config.id for existing in configs):
            raise ConfigurationError(f"MCP server {config.id!r} is already configured")
        self._write(configs + [config])
        return config

    def remove(self, server_id: str) -> MCPServerConfig:
        configs = self.list()
        removed = None
        kept: list[MCPServerConfig] = []
        for config in configs:
            if config.id == server_id:
                removed = config
            else:
                kept.append(config)
        if removed is None:
            raise ConfigurationError(f"unknown MCP server {server_id!r}")
        self._write(kept)
        return removed

    def enable(self, server_id: str) -> MCPServerConfig:
        return self.configure(server_id, enabled=True)

    def disable(self, server_id: str) -> MCPServerConfig:
        return self.configure(server_id, enabled=False)

    def configure(self, server_id: str, **updates: Any) -> MCPServerConfig:
        configs = self.list()
        updated: MCPServerConfig | None = None
        next_configs: list[MCPServerConfig] = []
        for config in configs:
            if config.id != server_id:
                next_configs.append(config)
                continue
            clean_updates = {key: value for key, value in updates.items() if value is not None}
            updated = replace(config, **clean_updates)
            next_configs.append(updated)
        if updated is None:
            raise ConfigurationError(f"unknown MCP server {server_id!r}")
        self._write(next_configs)
        return updated

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"servers": []}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, configs: list[MCPServerConfig]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"servers": [config.to_dict() for config in sorted(configs, key=lambda item: item.id)]}
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


__all__ = ["MCPServerConfig", "MCPServerRegistry"]
