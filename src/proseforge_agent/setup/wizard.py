"""Guided setup orchestration."""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

from .config_generator import SetupConfigGenerator, load_existing, provider_entry, redact_config_text
from .modes import PROVIDER_ORDER, SetupMode
from .recovery import backup_config, ensure_workspace


@dataclass(frozen=True)
class ProviderSetupResult:
    """Summary of one provider configured by guided setup."""

    name: str
    enabled: bool
    configured: bool
    status: Literal["ok", "skip", "fail", "warn"]
    latency_ms: int | None = None
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SetupResult:
    """Result returned by guided setup."""

    completed: bool
    mode: str
    config_path: Path
    workspace_path: Path
    providers: list[ProviderSetupResult] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)
    backup_path: Path | None = None
    rendered_config: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["config_path"] = str(self.config_path)
        payload["workspace_path"] = str(self.workspace_path)
        payload["backup_path"] = str(self.backup_path) if self.backup_path else None
        return payload


class SetupWizard:
    """Assemble install helpers into one non-destructive setup flow."""

    def __init__(
        self,
        root: str | Path | None = None,
        *,
        env: dict[str, str] | None = None,
        provider_ping=None,
        config_generator: SetupConfigGenerator | None = None,
    ) -> None:
        self.root = Path(root or ".pf-agent")
        self.env = dict(os.environ if env is None else env)
        self.provider_ping = provider_ping
        self.config_generator = config_generator or SetupConfigGenerator()

    def run(
        self,
        *,
        mode: SetupMode | str = SetupMode.QUICK,
        reconfigure: bool = False,
        add_provider: str | None = None,
        skip_provider_test: bool = False,
        no_shell: bool = False,
        repair: bool = False,
        print_config: bool = False,
    ) -> SetupResult:
        mode = SetupMode(mode)
        config_path = self.root / "config.yaml"
        workspace_path = self.root / "workspace"

        if print_config and config_path.exists():
            text = redact_config_text(config_path.read_text(encoding="utf-8"))
            return SetupResult(
                completed=True,
                mode=mode.value,
                config_path=config_path,
                workspace_path=workspace_path,
                next_steps=["pf-agent doctor"],
                rendered_config=text,
            )

        warnings: list[str] = []
        errors: list[str] = []
        backup_path = backup_config(config_path) if (reconfigure and config_path.exists()) else None
        existing = load_existing(config_path)
        ensure_workspace(workspace_path)

        selected = self._select_providers(mode, add_provider=add_provider)
        providers: list[ProviderSetupResult] = []
        provider_config: dict[str, dict[str, Any]] = {}
        for name in selected:
            result = self._configure_provider(name, skip_provider_test=skip_provider_test)
            providers.append(result)
            provider_config[name] = provider_entry(
                name,
                configured=result.configured,
                key_ref=_key_ref_for(name),
                status=result.status,
            )
            if result.status in {"warn", "fail"} and result.reason:
                warnings.append(f"{name}: {result.reason}")

        if "fake" not in provider_config:
            result = ProviderSetupResult("fake", True, True, "ok", reason="offline fallback")
            providers.append(result)
            provider_config["fake"] = provider_entry("fake", configured=True, status="ok")

        engine_enabled = bool(self.env.get("PROSEFORGE_ROOT"))
        if not engine_enabled:
            warnings.append("ProseForge engine not found; engine.enabled=false")
        if no_shell:
            warnings.append("shell completion registration skipped")
        if repair:
            warnings.append("repair checked workspace directories and setup flag")

        config = self.config_generator.build(
            mode=mode,
            workspace_path=workspace_path,
            providers=provider_config,
            existing=existing,
            engine_enabled=engine_enabled,
        )
        self.root.mkdir(parents=True, exist_ok=True)
        config_text = self.config_generator.render(config)
        config_path.write_text(config_text, encoding="utf-8")
        (self.root / ".env").write_text(
            self.config_generator.render_env_template(provider_config),
            encoding="utf-8",
        )

        return SetupResult(
            completed=not errors,
            mode=mode.value,
            config_path=config_path,
            workspace_path=workspace_path,
            providers=providers,
            warnings=warnings,
            errors=errors,
            next_steps=[
                "pf-agent doctor",
                "pf-agent chat --provider fake --message \"hello\"",
            ],
            backup_path=backup_path,
            rendered_config=redact_config_text(config_text),
        )

    def _select_providers(self, mode: SetupMode, *, add_provider: str | None) -> list[str]:
        if add_provider:
            return [_normalize_provider(add_provider), "fake"]
        if mode == SetupMode.MINIMAL:
            return ["fake"]
        if self.env.get("DEEPSEEK_API_KEY"):
            return ["deepseek", "fake"]
        if self.env.get("OPENAI_API_KEY"):
            return ["openai", "fake"]
        return ["fake"]

    def _configure_provider(self, name: str, *, skip_provider_test: bool) -> ProviderSetupResult:
        if name == "fake":
            return ProviderSetupResult("fake", True, True, "ok", reason="offline fallback")
        configured = bool(self.env.get(_env_key_for(name)))
        if skip_provider_test:
            return ProviderSetupResult(name, True, configured, "skip", reason="provider test skipped")
        if self.provider_ping is None:
            return ProviderSetupResult(
                name,
                True,
                configured,
                "ok" if configured else "warn",
                reason=None if configured else f"{_env_key_for(name)} is not set",
            )
        try:
            latency = self.provider_ping(name)
        except Exception as exc:  # noqa: BLE001 - provider ping is a warning, not a blocker
            return ProviderSetupResult(name, True, configured, "warn", reason=str(exc))
        return ProviderSetupResult(name, True, configured, "ok", latency_ms=int(latency or 0))


def _normalize_provider(name: str) -> str:
    return (name or "deepseek").lower().strip()


def _env_key_for(provider: str) -> str:
    return f"{provider.upper()}_API_KEY"


def _key_ref_for(provider: str) -> str | None:
    if provider == "fake":
        return None
    return f"env://{_env_key_for(provider)}"


__all__ = [
    "PROVIDER_ORDER",
    "ProviderSetupResult",
    "SetupResult",
    "SetupWizard",
]
