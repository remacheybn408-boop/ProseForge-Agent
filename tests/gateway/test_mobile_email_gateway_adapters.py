"""Mobile and email gateway adapter tests (Task 159)."""

from __future__ import annotations

from proseforge_agent.cli import main
from proseforge_agent.gateway import OutboundMessage
from proseforge_agent.gateway.platforms.email import EmailGatewayAdapter
from proseforge_agent.gateway.platforms.signal import SignalGatewayAdapter
from proseforge_agent.gateway.platforms.whatsapp import WhatsAppGatewayAdapter


def test_mobile_email_adapters_normalize_events():
    whatsapp_event = WhatsAppGatewayAdapter(api_key="wa-secret").parse_event(
        {
            "from": "whatsapp:+15551234567",
            "chat_id": "wa-chat",
            "message_id": "wa-1",
            "body": "hello whatsapp",
            "attachments": [{"type": "image", "ref": "media-1"}],
        }
    )
    signal_event = SignalGatewayAdapter(api_key="sig-secret").parse_event(
        {
            "source": "+15557654321",
            "group_id": "sig-group",
            "timestamp": "sig-1",
            "message": "hello signal",
        }
    )
    email_event = EmailGatewayAdapter(api_key="mail-secret").parse_event(
        {
            "from": "writer@example.com",
            "to": "agent@example.com",
            "message_id": "mail-1",
            "subject": "Draft",
            "body": "hello email",
            "attachments": [{"filename": "brief.pdf", "content_ref": "blob-1"}],
        }
    )

    assert whatsapp_event.platform == "whatsapp"
    assert signal_event.platform == "signal"
    assert email_event.platform == "email"
    assert whatsapp_event.attachments[0]["ref"] == "media-1"
    assert email_event.attachments[0]["content_ref"] == "blob-1"


def test_mobile_email_send_redacts_addresses_and_tokens():
    adapters = [
        WhatsAppGatewayAdapter(api_key="wa-secret", allow_fake_transport=True),
        SignalGatewayAdapter(api_key="sig-secret", allow_fake_transport=True),
        EmailGatewayAdapter(api_key="mail-secret", allow_fake_transport=True),
    ]

    for adapter in adapters:
        result = adapter.send(OutboundMessage(platform=adapter.platform, chat_id="user@example.com", thread_id="", text="reply"))
        assert result.delivered is True
        assert result.raw_metadata["api_key"] == "[redacted]"
        assert result.raw_metadata["recipient"] == "[redacted]"


def test_email_gateway_cli_check(capsys):
    assert main(["gateway", "email", "check", "--dry-run"]) == 0

    out = capsys.readouterr().out
    assert "Email Gateway" in out
    assert "dry_run=true" in out
