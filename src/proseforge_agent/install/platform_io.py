"""Portable shell quoting, UTF-8 IO, and terminal capability helpers."""

from __future__ import annotations

import re
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path

from ..errors import ConfigurationError


_SAFE = re.compile(r"^[A-Za-z0-9_./:=+-]+$")


class ShellCommandRenderer:
    """Render argv for common operator shells without leaving unsafe args bare."""

    def __init__(self, shell: str) -> None:
        self.shell = shell.lower()

    def render(self, argv: list[str]) -> str:
        if self.shell in {"bash", "zsh", "fish"}:
            return " ".join(shlex.quote(arg) for arg in argv)
        if self.shell == "powershell":
            return " ".join(_quote_powershell(arg) for arg in argv)
        if self.shell == "cmd":
            return " ".join(_quote_cmd(arg) for arg in argv)
        raise ConfigurationError(f"unknown shell {self.shell!r}")


@dataclass(frozen=True)
class TerminalCaps:
    """Detected terminal output capabilities."""

    supports_utf8: bool
    ascii_fallback: bool = False

    @classmethod
    def detect(cls, env: dict[str, str] | None = None) -> "TerminalCaps":
        env = dict(env or {})
        if env.get("WT_SESSION") or env.get("PYTHONUTF8") == "1":
            return cls(supports_utf8=True)
        if (env.get("COMSPEC") or "").lower().endswith("cmd.exe"):
            return cls(supports_utf8=False, ascii_fallback=True)
        encoding = (getattr(sys.stdout, "encoding", None) or "").lower()
        supports = "utf" in encoding
        return cls(supports_utf8=supports, ascii_fallback=not supports)


def write_text_utf8(path: Path | str, text: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def read_text_utf8(path: Path | str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _quote_powershell(arg: str) -> str:
    if _SAFE.match(arg):
        return arg
    return "'" + arg.replace("'", "''") + "'"


def _quote_cmd(arg: str) -> str:
    if _SAFE.match(arg):
        return arg
    return '"' + arg.replace('"', '""') + '"'


__all__ = ["ShellCommandRenderer", "TerminalCaps", "read_text_utf8", "write_text_utf8"]
