import json
from pathlib import Path

import pytest

from proseforge_agent.agent.modes import CONVERSATION_MODES
from proseforge_agent.chat.prompts import ChatPromptBuilder, PromptPack
from proseforge_agent.cli import main
from proseforge_agent.errors import ConfigurationError


FIXTURE = Path(__file__).parent / "fixtures" / "chat-prompt-protocol" / "evidence_pack.json"


def test_prompt_builder_supports_all_conversation_modes():
    builder = ChatPromptBuilder()
    for mode in CONVERSATION_MODES:
        pack = builder.build(text="hello", mode=mode)
        assert isinstance(pack, PromptPack)
        assert pack.mode == mode
        assert mode in pack.system


def test_prompt_pack_keeps_canon_and_suggestions_separate():
    evidence_pack = json.loads(FIXTURE.read_text(encoding="utf-8"))
    pack = ChatPromptBuilder().build(
        text="今天写什么？",
        mode="project_chat",
        project_slug="demo",
        evidence_pack=evidence_pack,
    )
    rendered = pack.render_markdown()
    canon_block = rendered.split("## Suggestions", maxsplit=1)[0]
    suggestions_block = rendered.split("## Suggestions", maxsplit=1)[1]
    assert "主角已经抵达上海" in canon_block
    assert "雨天氛围" not in canon_block
    assert "雨天氛围" in suggestions_block


def test_prompt_pack_to_dict_is_stable_for_cli_json():
    evidence_pack = json.loads(FIXTURE.read_text(encoding="utf-8"))
    payload = ChatPromptBuilder().build(
        text="继续第二章",
        mode="creative_chat",
        evidence_pack=evidence_pack,
    ).to_dict()
    assert payload["mode"] == "creative_chat"
    assert payload["canon"][0]["kind"] == "canon"
    assert payload["suggestions"][0]["kind"] == "suggestion"


def test_prompt_builder_rejects_unknown_mode():
    with pytest.raises(ConfigurationError):
        ChatPromptBuilder().build(text="hello", mode="unknown")


def test_show_prompt_cli_prints_prompt_pack(capsys):
    code = main(
        [
            "chat",
            "--message",
            "今天写什么？",
            "--project",
            "demo",
            "--provider",
            "fake",
            "--show-prompt",
        ]
    )
    out = capsys.readouterr().out
    assert code == 0
    assert "Prompt Pack" in out
    assert "## Canon" in out
    assert "## Suggestions" in out
    assert "Agent Chat" not in out
