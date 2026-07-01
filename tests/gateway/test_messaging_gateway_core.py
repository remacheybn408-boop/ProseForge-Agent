"""Messaging gateway core tests (Task 155)."""

from __future__ import annotations

import json

from proseforge_agent.cli import main
from proseforge_agent.gateway import GatewayRunner, MessageEvent


def test_gateway_routes_message_to_agent_session(tmp_path):
    runner = GatewayRunner(root=tmp_path / ".pf-agent", provider_name="fake")
    event = MessageEvent(
        platform="telegram",
        chat_id="chat-1",
        user_id="user-1",
        thread_id="topic-1",
        message_id="msg-1",
        text="hello gateway",
        authorization={"allowed": True},
    )

    result = runner.handle_event(event)

    assert result.status == "queued"
    assert result.session_id == "gateway_telegram_chat-1_topic-1"
    context = runner.session_store.load_context(result.session_id)
    assert context.messages[0].role == "user"
    assert context.messages[0].content == "hello gateway"
    assert result.delivery_jobs[0].platform == "telegram"
    queue_rows = (tmp_path / ".pf-agent" / "gateway" / "deliveries.jsonl").read_text(encoding="utf-8").splitlines()
    assert json.loads(queue_rows[0])["chat_id"] == "chat-1"


def test_gateway_denies_unauthorized_user_without_session(tmp_path):
    runner = GatewayRunner(root=tmp_path / ".pf-agent", allowed_users={"known-user"})

    result = runner.handle_event(
        MessageEvent(
            platform="telegram",
            chat_id="chat-1",
            user_id="unknown-user",
            thread_id="",
            message_id="msg-1",
            text="hello",
        )
    )

    assert result.status == "denied"
    assert runner.session_store.list() == []


def test_gateway_cli_check_mode(capsys):
    assert main(["gateway", "run", "--provider", "fake", "--check"]) == 0

    out = capsys.readouterr().out
    assert "Gateway" in out
    assert "provider=fake" in out
