"""Prompt template registry tests (Task 113)."""

from __future__ import annotations

import pytest

from proseforge_agent.agent.prompt_templates import (
    PromptTemplateRegistry,
    PromptTemplateValidationError,
)
from proseforge_agent.cli import main


def test_prompt_template_registry_contract():
    registry = PromptTemplateRegistry.builtins()

    assert registry.ids() == [
        "condense_chapter_v1",
        "continuity_check_v1",
        "draft_chapter_v1",
        "expand_scene_v1",
        "reader_review_v1",
        "review_chapter_v1",
        "rewrite_v1",
        "title_suggestion_v1",
    ]

    template = registry.get("draft_chapter_v1")
    assert template.version == "1"
    assert template.variables == ["chapter_number", "brief"]
    assert template.required_evidence == ["canon", "outline"]
    assert template.supports_provider("fake")

    validation = registry.validate(
        "draft_chapter_v1",
        variables={"chapter_number": "3", "brief": "open with a storm"},
        evidence={"canon": ["The city is coastal."], "outline": ["Chapter 3 escape."]},
        provider="fake",
    )
    assert validation.valid is True
    assert validation.missing_variables == []
    assert validation.missing_evidence == []

    rendered = registry.render(
        "draft_chapter_v1",
        variables={"chapter_number": "3", "brief": "open with a storm"},
        evidence={"canon": ["The city is coastal."], "outline": ["Chapter 3 escape."]},
        provider="fake",
    )
    assert "Chapter 3" in rendered
    assert "The city is coastal." in rendered


def test_prompt_template_validation_reports_missing_inputs():
    registry = PromptTemplateRegistry.builtins()

    result = registry.validate("draft_chapter_v1", variables={"brief": "x"}, evidence={}, provider="fake")

    assert result.valid is False
    assert result.missing_variables == ["chapter_number"]
    assert result.missing_evidence == ["canon", "outline"]
    assert result.errors


def test_prompt_template_rejects_incompatible_provider():
    registry = PromptTemplateRegistry.builtins()

    with pytest.raises(PromptTemplateValidationError):
        registry.render(
            "draft_chapter_v1",
            variables={"chapter_number": "3", "brief": "x"},
            evidence={"canon": ["c"], "outline": ["o"]},
            provider="unknown-provider",
        )


def test_prompt_template_cli_list_and_validate(capsys):
    assert main(["prompt-template", "list"]) == 0
    assert main(["prompt-template", "validate", "draft_chapter_v1"]) == 0

    out = capsys.readouterr().out
    assert "draft_chapter_v1" in out
    assert "Prompt Template Validation" in out
