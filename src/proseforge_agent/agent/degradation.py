"""Graceful feature degradation and runtime capability reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import IntEnum
from typing import Any


class FeatureLevel(IntEnum):
    """Ordered runtime capability levels."""

    OFFLINE = 0
    LOCAL_MODEL = 1
    REMOTE_PROVIDER = 2

    @property
    def label(self) -> str:
        return {
            FeatureLevel.OFFLINE: "offline",
            FeatureLevel.LOCAL_MODEL: "local_model",
            FeatureLevel.REMOTE_PROVIDER: "remote_provider",
        }[self]


@dataclass(frozen=True)
class FeatureDeclaration:
    """Capability requirement for a feature."""

    id: str
    required_level: FeatureLevel
    dependencies: list[str] = field(default_factory=list)
    guidance: str = ""


@dataclass(frozen=True)
class FeatureCheck:
    """Decision for one feature under current runtime capabilities."""

    feature_id: str
    allowed: bool
    status: str
    required_level: str
    available_level: str
    guidance: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CapabilityReport:
    """Runtime capability report for all declared features."""

    available_level: str
    features: dict[str, dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


DEFAULT_FEATURES = {
    "export_txt": FeatureDeclaration(
        id="export_txt",
        required_level=FeatureLevel.OFFLINE,
        guidance="TXT/Markdown export can run offline.",
    ),
    "manifest_validate": FeatureDeclaration(
        id="manifest_validate",
        required_level=FeatureLevel.OFFLINE,
        guidance="Manifest validation can run offline.",
    ),
    "keyword_search": FeatureDeclaration(
        id="keyword_search",
        required_level=FeatureLevel.OFFLINE,
        guidance="Keyword search can run from local text indexes.",
    ),
    "stats": FeatureDeclaration(
        id="stats",
        required_level=FeatureLevel.OFFLINE,
        guidance="Writing stats can run from local project files.",
    ),
    "backup": FeatureDeclaration(
        id="backup",
        required_level=FeatureLevel.OFFLINE,
        guidance="Backups can run without provider access.",
    ),
    "fake_chat": FeatureDeclaration(
        id="fake_chat",
        required_level=FeatureLevel.OFFLINE,
        guidance="Fake provider chat can run offline.",
    ),
    "rewrite": FeatureDeclaration(
        id="rewrite",
        required_level=FeatureLevel.LOCAL_MODEL,
        dependencies=["provider"],
        guidance="Rewrite requires provider capability; use fake chat or export while offline.",
    ),
    "cloud_sync": FeatureDeclaration(
        id="cloud_sync",
        required_level=FeatureLevel.REMOTE_PROVIDER,
        dependencies=["network"],
        guidance="Cloud sync requires network connectivity.",
    ),
}


class CapabilityRuntime:
    """Evaluate features against the current runtime capability level."""

    def __init__(
        self,
        *,
        available_level: FeatureLevel = FeatureLevel.OFFLINE,
        dependencies: dict[str, bool] | None = None,
        declarations: dict[str, FeatureDeclaration] | None = None,
    ) -> None:
        self.available_level = available_level
        self.dependencies = dependencies or {}
        self.declarations = declarations or DEFAULT_FEATURES

    def check(self, feature_id: str) -> FeatureCheck:
        declaration = self.declarations[feature_id]
        missing = [name for name in declaration.dependencies if not self.dependencies.get(name, False)]
        if self.available_level < declaration.required_level:
            return FeatureCheck(
                feature_id=feature_id,
                allowed=False,
                status="degraded",
                required_level=declaration.required_level.label,
                available_level=self.available_level.label,
                guidance=declaration.guidance,
            )
        if missing:
            return FeatureCheck(
                feature_id=feature_id,
                allowed=False,
                status="degraded",
                required_level=declaration.required_level.label,
                available_level=self.available_level.label,
                guidance=f"requires {', '.join(missing)}; {declaration.guidance}",
            )
        return FeatureCheck(
            feature_id=feature_id,
            allowed=True,
            status="ok",
            required_level=declaration.required_level.label,
            available_level=self.available_level.label,
            guidance=declaration.guidance,
        )

    def report(self) -> CapabilityReport:
        return CapabilityReport(
            available_level=self.available_level.label,
            features={feature_id: self.check(feature_id).to_dict() for feature_id in sorted(self.declarations)},
        )


__all__ = [
    "CapabilityReport",
    "CapabilityRuntime",
    "DEFAULT_FEATURES",
    "FeatureCheck",
    "FeatureDeclaration",
    "FeatureLevel",
]
