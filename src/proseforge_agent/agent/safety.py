"""Prompt-injection and permission-escalation guard for untrusted content.

The agent reads project files, durable memory, and chat input. Text inside that
content must never be able to hijack the agent's tools or raise its permission
ceiling. :class:`InjectionGuard` inspects content with a provenance label
(``trusted`` vs ``untrusted``), scans for tool-invocation and
permission-escalation patterns in both Chinese and English, and returns a
:class:`SafetyVerdict` the kernel must honour before acting.

Core rules:

* Untrusted content can only *lower* the allowed ceiling; it can never raise it
  above the session's granted level.
* Instructions embedded in untrusted text are treated as data, never executed;
  detecting them forces the ceiling to ``read_only`` for that turn.
* Trusted content (the user is the principal) keeps the session-granted ceiling.

The guard never calls a provider and never mutates the content it inspects.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .permissions import PERMISSION_LEVELS

_ORDER = {name: index for index, name in enumerate(PERMISSION_LEVELS)}
_FLOOR = PERMISSION_LEVELS[0]  # "read_only"


def _min_ceiling(a: str, b: str) -> str:
    """Return the lower (more restrictive) of two permission levels."""
    return a if _ORDER.get(a, 0) <= _ORDER.get(b, 0) else b


# Patterns that try to override prior instructions / escalate authority.
_ESCALATION_PATTERNS: tuple[re.Pattern, ...] = (
    re.compile(r"ignore\s+(all\s+|the\s+)?(previous|prior|above|earlier)\s+(instructions?|rules?|settings?)", re.I),
    re.compile(r"disregard\s+(all\s+|the\s+)?(previous|prior|above|earlier)", re.I),
    re.compile(r"you\s+are\s+now\b", re.I),
    re.compile(r"new\s+(system\s+)?(instructions?|prompt)", re.I),
    re.compile(r"\b(grant|raise|elevate)\s+(me\s+)?(permission|access|privileges?)", re.I),
    re.compile(r"\bsystem[_\s-]?write\b", re.I),
    re.compile(r"忽略(以上|上面|之前|前面|先前)?.{0,6}(设定|指令|规则|要求|提示)"),
    re.compile(r"无视(以上|上面|之前|前面)?.{0,6}(设定|指令|规则)"),
    re.compile(r"现在你是"),
    re.compile(r"(提升|提高|获取).{0,4}(权限|权利)"),
)

# Patterns that try to invoke a tool / workflow action.
_TOOL_INVOCATION_PATTERNS: tuple[re.Pattern, ...] = (
    # imperative verb + dotted tool name, e.g. "execute workflow.start"
    re.compile(r"\b(run|execute|invoke|call|trigger|start)\s+[a-z_]+\.[a-z_]+", re.I),
    re.compile(r"(执行|运行|调用|启动|触发)\s*[a-z_]+\.[a-z_]+", re.I),
    # NOTE: a bare "(现在)?(执行|运行|调用|启动)" pattern was removed here — it
    # matched ordinary novel prose ("主角执行了命令", "计划启动了") and forced
    # untrusted content down to read_only. The dotted-tool-token pattern above
    # already catches real invocations. See finding 1.2 / core-review-2026-07-01.
    re.compile(r"\baccept\s+all\s+chapters?\b", re.I),
    re.compile(r"接受所有章节"),
    re.compile(r"\b(workflow\.start|chapter\.accept|draft\.note)\b", re.I),
)


@dataclass(frozen=True)
class SafetyVerdict:
    """Result of assessing one piece of content for the kernel to honour."""

    provenance: str
    allowed_ceiling: str
    flags: tuple[str, ...] = field(default_factory=tuple)
    reason: str = ""

    @property
    def is_flagged(self) -> bool:
        return bool(self.flags)

    def to_dict(self) -> dict:
        return {
            "provenance": self.provenance,
            "allowed_ceiling": self.allowed_ceiling,
            "flags": list(self.flags),
            "reason": self.reason,
        }


class InjectionGuard:
    """Assess content provenance and compute the permission ceiling for a turn."""

    def _scan(self, content: str) -> list[str]:
        flags: list[str] = []
        if any(pattern.search(content) for pattern in _TOOL_INVOCATION_PATTERNS):
            flags.append("tool_invocation_attempt")
        if any(pattern.search(content) for pattern in _ESCALATION_PATTERNS):
            flags.append("permission_escalation_attempt")
        return flags

    def assess(
        self,
        content: str,
        provenance: str,
        session_ceiling: str = _FLOOR,
    ) -> SafetyVerdict:
        """Return a :class:`SafetyVerdict` for ``content``.

        ``provenance`` is ``"trusted"`` (the user/principal) or ``"untrusted"``
        (retrieved evidence, file text, pasted content). ``session_ceiling`` is
        the maximum permission the session has been granted; the verdict can
        never exceed it.
        """
        content = content or ""
        if provenance != "untrusted":
            # Trusted content keeps the session grant; embedded patterns are not
            # used to escalate, but we still surface flags for transparency.
            return SafetyVerdict(
                provenance="trusted",
                allowed_ceiling=session_ceiling,
                flags=tuple(self._scan(content)),
                reason="trusted content keeps the session-granted ceiling",
            )

        flags = self._scan(content)
        if flags:
            # Embedded instructions are treated as data, never executed: detecting
            # them forces the ceiling to read_only for this turn.
            ceiling = _min_ceiling(_FLOOR, session_ceiling)
            reason = (
                "untrusted content contains injection patterns "
                f"({', '.join(flags)}); treated as data and forced to {ceiling}"
            )
        else:
            # Clean untrusted content does not lower the ceiling, but it can never
            # raise it above the session grant.
            ceiling = session_ceiling
            reason = "untrusted content is clean; ceiling capped at the session grant"

        return SafetyVerdict(
            provenance="untrusted",
            allowed_ceiling=ceiling,
            flags=tuple(flags),
            reason=reason,
        )


__all__ = ["SafetyVerdict", "InjectionGuard"]
