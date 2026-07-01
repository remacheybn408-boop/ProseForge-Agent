"""Gateway relay auth and pairing tests (Task 160)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from proseforge_agent.cli import main
from proseforge_agent.gateway.relay import RelayAuthenticator, RelayPairingService


def test_pairing_token_is_scoped_and_redacted():
    service = RelayPairingService(secret="local-secret")

    token = service.create_pairing_token(
        gateway_instance_id="gw-1",
        profile="operator",
        platform="telegram",
        ttl_seconds=60,
    )
    public = token.redacted()

    assert token.gateway_instance_id == "gw-1"
    assert token.profile == "operator"
    assert token.platform == "telegram"
    assert token.raw_token not in public
    assert public.endswith("[redacted]")
    assert "telegram" in public


def test_relay_auth_rejects_wrong_audience_expired_and_revoked():
    service = RelayPairingService(secret="local-secret")
    token = service.create_pairing_token(
        gateway_instance_id="gw-1",
        profile="operator",
        platform="telegram",
        expires_at=datetime.now(UTC) + timedelta(seconds=60),
    )
    authenticator = RelayAuthenticator(secret="local-secret")

    assert authenticator.validate(token.raw_token, gateway_instance_id="gw-1", platform="telegram").allowed is True
    assert authenticator.validate(token.raw_token, gateway_instance_id="gw-2", platform="telegram").allowed is False
    assert authenticator.validate(token.raw_token, gateway_instance_id="gw-1", platform="slack").allowed is False
    authenticator.revoke(token.raw_token)
    assert authenticator.validate(token.raw_token, gateway_instance_id="gw-1", platform="telegram").allowed is False

    expired = service.create_pairing_token(
        gateway_instance_id="gw-1",
        profile="operator",
        platform="telegram",
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
    )
    assert authenticator.validate(expired.raw_token, gateway_instance_id="gw-1", platform="telegram").allowed is False


def test_relay_sanitizes_inbound_event():
    authenticator = RelayAuthenticator(secret="local-secret")
    event = authenticator.sanitize_event(
        {
            "platform": "telegram",
            "chat_id": "12345",
            "text": "hello",
            "token": "platform-secret",
            "authorization": "Bearer secret",
        }
    )

    assert event["token"] == "[redacted]"
    assert event["authorization"] == "[redacted]"
    assert event["chat_id"] == "[redacted]"


def test_gateway_relay_cli_check(capsys):
    assert main(["gateway", "relay", "check", "--dry-run"]) == 0

    out = capsys.readouterr().out
    assert "Gateway Relay" in out
    assert "dry_run=true" in out
