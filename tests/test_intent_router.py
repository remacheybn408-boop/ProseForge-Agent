from pathlib import Path

import pytest
import yaml

from proseforge_agent.agent.intent_router import IntentRouter
from proseforge_agent.agent.modes import CONVERSATION_MODES, INTENT_NAMES
from proseforge_agent.cli import main
from proseforge_agent.errors import ConfigurationError


FIXTURE = Path(__file__).parent / "fixtures" / "agent" / "intent_cases.yaml"


def test_operator_chat_detects_install_diagnosis():
    router = IntentRouter()
    decision = router.classify("为什么 provider key 读不到？", mode="operator_chat")
    assert decision.name == "diagnose_installation"
    assert decision.required_permission == "read_only"
    assert "provider" in decision.reason.lower()


def test_general_chat_answers_without_project_context():
    decision = IntentRouter().classify("hello there", mode="general_chat")
    assert decision.name == "answer_directly"
    assert decision.required_permission == "read_only"


def test_project_chat_retrieves_context_for_today_question():
    decision = IntentRouter().classify("今天应该写什么？", mode="project_chat")
    assert decision.name == "retrieve_context"
    assert decision.required_permission == "read_only"


def test_workflow_chat_requires_permission_for_continue():
    decision = IntentRouter().classify("continue workflow run", mode="workflow_chat")
    assert decision.name == "continue_workflow"
    assert decision.required_permission == "project_write"
    assert decision.target_tool == "workflow.continue"


def test_creative_chat_creates_memory_candidate_intent():
    decision = IntentRouter().classify("remember this style preference", mode="creative_chat")
    assert decision.name == "update_memory_candidate"
    assert decision.required_permission == "draft_write"


def test_switch_mode_from_general_to_project_requires_project_slug():
    decision = IntentRouter().classify("switch to project chat", mode="general_chat")
    assert decision.name == "ask_clarifying_question"
    assert "project" in decision.reason.lower()


def test_ambiguous_write_request_asks_clarifying_question():
    decision = IntentRouter().classify("write it", mode="general_chat")
    assert decision.name == "ask_clarifying_question"
    assert decision.required_permission == "read_only"


def test_unknown_mode_fails_before_provider_calls():
    with pytest.raises(ConfigurationError):
        IntentRouter().classify("hello", mode="bogus")


def test_mode_and_intent_names_are_ascii_safe():
    assert {"general_chat", "project_chat", "workflow_chat", "operator_chat", "creative_chat"} <= set(CONVERSATION_MODES)
    assert {"answer_directly", "diagnose_installation", "ask_clarifying_question"} <= set(INTENT_NAMES)


def test_intent_fixture_contains_chinese_and_english_cases():
    data = yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))
    texts = [case["text"] for case in data["cases"]]
    assert any("provider" in text for text in texts)
    assert any("今天" in text for text in texts)


def test_chat_classify_cli_prints_intent(capsys):
    code = main(["chat", "classify", "--mode", "operator_chat", "--text", "provider key 读不到"])
    out = capsys.readouterr().out
    assert code == 0
    assert "diagnose_installation" in out
