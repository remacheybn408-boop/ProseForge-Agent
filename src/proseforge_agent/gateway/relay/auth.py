"""Scoped relay pairing tokens and validation."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from typing import Any


_SENSITIVE_KEYS = {"token", "authorization", "api_key", "secret", "password", "chat_id", "user_id"}


@dataclass(frozen=True)
class PairingToken:
    raw_token: str
    gateway_instance_id: str
    profile: str
    platform: str
    expires_at: str

    def redacted(self) -> str:
        prefix = self.raw_token[:10] if self.raw_token else ""
        return f"{self.platform}:{self.gateway_instance_id}:{self.profile}:{prefix}[redacted]"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["raw_token"] = self.redacted()
        return payload


@dataclass(frozen=True)
class RelayAuthDecision:
    allowed: bool
    reason: str
    profile: str = ""
    platform: str = ""
    gateway_instance_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class RelayPairingService:
    """Create scoped relay pairing credentials."""

    def __init__(self, *, secret: str) -> None:
        self.secret = secret.encode("utf-8")

    def create_pairing_token(
        self,
        *,
        gateway_instance_id: str,
        profile: str,
        platform: str,
        ttl_seconds: int = 3600,
        expires_at: datetime | None = None,
    ) -> PairingToken:
        expiry = expires_at or (datetime.now(UTC) + timedelta(seconds=ttl_seconds))
        payload = {
            "gateway_instance_id": gateway_instance_id,
            "profile": profile,
            "platform": platform,
            "expires_at": expiry.isoformat(),
        }
        raw_token = _encode_token(payload, self.secret)
        return PairingToken(
            raw_token=raw_token,
            gateway_instance_id=gateway_instance_id,
            profile=profile,
            platform=platform,
            expires_at=payload["expires_at"],
        )


class RelayAuthenticator:
    """Validate relay tokens and sanitize relay events."""

    def __init__(self, *, secret: str) -> None:
        self.secret = secret.encode("utf-8")
        self._revoked: set[str] = set()

    def revoke(self, raw_token: str) -> None:
        self._revoked.add(_fingerprint(raw_token))

    def validate(self, raw_token: str, *, gateway_instance_id: str, platform: str) -> RelayAuthDecision:
        if _fingerprint(raw_token) in self._revoked:
            return RelayAuthDecision(False, "token revoked")
        try:
            payload = _decode_token(raw_token, self.secret)
        except ValueError as exc:
            return RelayAuthDecision(False, str(exc))
        if payload.get("gateway_instance_id") != gateway_instance_id:
            return RelayAuthDecision(False, "wrong gateway instance")
        if payload.get("platform") != platform:
            return RelayAuthDecision(False, "wrong platform audience")
        expires_at = datetime.fromisoformat(str(payload.get("expires_at")))
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at <= datetime.now(UTC):
            return RelayAuthDecision(False, "token expired")
        return RelayAuthDecision(
            True,
            "token accepted",
            profile=str(payload.get("profile", "")),
            platform=platform,
            gateway_instance_id=gateway_instance_id,
        )

    def sanitize_event(self, event: dict[str, Any]) -> dict[str, Any]:
        return _sanitize(event)


def _encode_token(payload: dict[str, Any], secret: bytes) -> str:
    body = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    encoded_body = base64.urlsafe_b64encode(body).decode("ascii").rstrip("=")
    signature = hmac.new(secret, encoded_body.encode("ascii"), hashlib.sha256).hexdigest()
    return f"pfr.{encoded_body}.{signature}"


def _decode_token(raw_token: str, secret: bytes) -> dict[str, Any]:
    try:
        prefix, encoded_body, signature = raw_token.split(".", 2)
    except ValueError as exc:
        raise ValueError("invalid token format") from exc
    if prefix != "pfr":
        raise ValueError("invalid token prefix")
    expected = hmac.new(secret, encoded_body.encode("ascii"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise ValueError("invalid token signature")
    padded = encoded_body + "=" * (-len(encoded_body) % 4)
    return json.loads(base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8"))


def _fingerprint(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            sanitized[key] = "[redacted]" if str(key).lower() in _SENSITIVE_KEYS else _sanitize(item)
        return sanitized
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    return value


__all__ = ["PairingToken", "RelayAuthDecision", "RelayAuthenticator", "RelayPairingService"]
