"""Workflow prompt template registry."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from ..errors import ConfigurationError


class PromptTemplateValidationError(ConfigurationError):
    """Raised when a prompt template cannot be rendered safely."""


@dataclass(frozen=True)
class PromptTemplate:
    """A reusable workflow prompt template definition."""

    id: str
    version: str
    text: str
    variables: list[str] = field(default_factory=list)
    required_evidence: list[str] = field(default_factory=list)
    provider_compatibility: list[str] = field(default_factory=lambda: ["fake"])
    changelog: list[str] = field(default_factory=list)

    def supports_provider(self, provider: str) -> bool:
        return "*" in self.provider_compatibility or provider in self.provider_compatibility

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PromptTemplateValidation:
    """Structured validation report for runtime prompt inputs."""

    template_id: str
    valid: bool
    provider: str
    missing_variables: list[str] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PromptTemplateRegistry:
    """Central registry for workflow prompt templates."""

    def __init__(self, templates: list[PromptTemplate]) -> None:
        self._templates = {template.id: template for template in templates}

    @classmethod
    def builtins(cls) -> "PromptTemplateRegistry":
        providers = ["fake", "openai", "anthropic", "gemini"]
        return cls(
            [
                PromptTemplate(
                    id="draft_chapter_v1",
                    version="1",
                    text=(
                        "Draft Chapter {chapter_number}.\n"
                        "Brief: {brief}\n\n"
                        "{evidence}"
                    ),
                    variables=["chapter_number", "brief"],
                    required_evidence=["canon", "outline"],
                    provider_compatibility=providers,
                    changelog=["initial draft chapter template"],
                ),
                PromptTemplate(
                    id="review_chapter_v1",
                    version="1",
                    text="Review chapter prose against canon and writing rules.\n\n{evidence}",
                    variables=["chapter_id"],
                    required_evidence=["draft", "rules"],
                    provider_compatibility=providers,
                    changelog=["initial review template"],
                ),
                PromptTemplate(
                    id="rewrite_v1",
                    version="1",
                    text="Rewrite the passage using strategy {strategy}.\n\n{evidence}",
                    variables=["strategy"],
                    required_evidence=["passage"],
                    provider_compatibility=providers,
                    changelog=["initial rewrite template"],
                ),
                PromptTemplate(
                    id="expand_scene_v1",
                    version="1",
                    text="Expand scene {scene_id} while preserving constraints.\n\n{evidence}",
                    variables=["scene_id"],
                    required_evidence=["scene", "canon"],
                    provider_compatibility=providers,
                    changelog=["initial scene expansion template"],
                ),
                PromptTemplate(
                    id="condense_chapter_v1",
                    version="1",
                    text="Condense chapter {chapter_id} without losing plot-critical beats.\n\n{evidence}",
                    variables=["chapter_id"],
                    required_evidence=["chapter", "plot_threads"],
                    provider_compatibility=providers,
                    changelog=["initial chapter condensation template"],
                ),
                PromptTemplate(
                    id="title_suggestion_v1",
                    version="1",
                    text="Suggest titles for {work_type} using tone {tone}.\n\n{evidence}",
                    variables=["work_type", "tone"],
                    required_evidence=["summary"],
                    provider_compatibility=providers,
                    changelog=["initial title suggestion template"],
                ),
                PromptTemplate(
                    id="continuity_check_v1",
                    version="1",
                    text="Check continuity for {scope} and report conflicts.\n\n{evidence}",
                    variables=["scope"],
                    required_evidence=["canon", "timeline"],
                    provider_compatibility=providers,
                    changelog=["initial continuity template"],
                ),
                PromptTemplate(
                    id="reader_review_v1",
                    version="1",
                    text="Give a reader review from the {reader_profile} perspective.\n\n{evidence}",
                    variables=["reader_profile"],
                    required_evidence=["chapter"],
                    provider_compatibility=providers,
                    changelog=["initial reader review template"],
                ),
            ]
        )

    def ids(self) -> list[str]:
        return sorted(self._templates)

    def list(self) -> list[PromptTemplate]:
        return [self._templates[template_id] for template_id in self.ids()]

    def get(self, template_id: str) -> PromptTemplate:
        template = self._templates.get(template_id)
        if template is None:
            raise ConfigurationError(f"unknown prompt template {template_id!r}")
        return template

    def validate(
        self,
        template_id: str,
        *,
        variables: dict[str, Any] | None = None,
        evidence: dict[str, Any] | None = None,
        provider: str = "fake",
    ) -> PromptTemplateValidation:
        template = self.get(template_id)
        variables = variables or {}
        evidence = evidence or {}
        missing_variables = [name for name in template.variables if not variables.get(name)]
        missing_evidence = [name for name in template.required_evidence if not evidence.get(name)]
        errors: list[str] = []
        if missing_variables:
            errors.append(f"missing variables: {', '.join(missing_variables)}")
        if missing_evidence:
            errors.append(f"missing evidence: {', '.join(missing_evidence)}")
        if not template.supports_provider(provider):
            errors.append(f"provider {provider!r} is not compatible")
        return PromptTemplateValidation(
            template_id=template.id,
            valid=not errors,
            provider=provider,
            missing_variables=missing_variables,
            missing_evidence=missing_evidence,
            errors=errors,
        )

    def validate_definition(self, template_id: str) -> PromptTemplateValidation:
        template = self.get(template_id)
        errors: list[str] = []
        if not template.version:
            errors.append("missing version")
        if "{evidence}" not in template.text:
            errors.append("template must include {evidence}")
        return PromptTemplateValidation(
            template_id=template.id,
            valid=not errors,
            provider="definition",
            errors=errors,
        )

    def render(
        self,
        template_id: str,
        *,
        variables: dict[str, Any] | None = None,
        evidence: dict[str, Any] | None = None,
        provider: str = "fake",
    ) -> str:
        template = self.get(template_id)
        variables = variables or {}
        evidence = evidence or {}
        validation = self.validate(template_id, variables=variables, evidence=evidence, provider=provider)
        if not validation.valid:
            raise PromptTemplateValidationError("; ".join(validation.errors))
        values = {name: str(variables[name]) for name in template.variables}
        values["evidence"] = _render_evidence(evidence)
        return template.text.format(**values)


def _render_evidence(evidence: dict[str, Any]) -> str:
    lines: list[str] = []
    for key in sorted(evidence):
        lines.append(f"## Evidence: {key}")
        value = evidence[key]
        if isinstance(value, list):
            lines.extend(f"- {item}" for item in value)
        else:
            lines.append(str(value))
    return "\n".join(lines)


__all__ = [
    "PromptTemplate",
    "PromptTemplateRegistry",
    "PromptTemplateValidation",
    "PromptTemplateValidationError",
]
