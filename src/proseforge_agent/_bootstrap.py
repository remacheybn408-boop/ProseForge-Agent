"""Early process bootstrap (Task 190).

Fixes Windows text-encoding issues before any user-facing output and hardens
the import path. Imported as the very first line of every entry point
(``cli``, ``chat.repl``, ``demo``, ``__main__``) so a UTF-8-safe interpreter is
guaranteed before the rest of the package loads.

Four responsibilities, each guarded so the bootstrap NEVER raises:

1. Force UTF-8 for child processes (``PYTHONUTF8``, ``PYTHONIOENCODING``).
2. Reconfigure stdout/stderr/stdin to UTF-8 with ``errors="replace"``.
3. Harden ``sys.path`` (prepend the package source root, strip ``""``/``.``).
4. Record everything in :data:`STATE` for observability.

Safe to import multiple times: a guard on ``sys._pf_agent_bootstrapped``
makes repeat calls a no-op.
"""

from __future__ import annotations

import os
import sys
from typing import Any


STATE: dict[str, Any] = {
    "already_installed": False,
    "python_utf8_set": None,
    "stdout_reconfigured": None,
    "stderr_reconfigured": None,
    "stdin_reconfigured": None,
    "sys_path_hardened": False,
    "warnings": [],
}


def _configure_utf8_env() -> None:
    if "PYTHONUTF8" in os.environ:
        STATE["python_utf8_set"] = "preexisting"
    else:
        os.environ["PYTHONUTF8"] = "1"
        STATE["python_utf8_set"] = True
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")


def _reconfigure_stream(name: str, key: str) -> None:
    stream = getattr(sys, name, None)
    reconfigure = getattr(stream, "reconfigure", None)
    if not callable(reconfigure):
        STATE[key] = "not_a_text_wrapper"
        return
    try:
        reconfigure(encoding="utf-8", errors="replace")
        STATE[key] = True
    except Exception as exc:  # noqa: BLE001 - bootstrap must never raise
        STATE[key] = False
        STATE["warnings"].append(f"{name}.reconfigure failed: {exc}")


def _harden_sys_path() -> None:
    try:
        src_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if src_root and src_root not in sys.path:
            sys.path.insert(0, src_root)
        # Strip current-directory entries so a user's local module cannot
        # shadow package modules with common names (utils, proxy, ui, ...).
        sys.path[:] = [entry for entry in sys.path if entry not in ("", ".")]
        STATE["sys_path_hardened"] = True
    except Exception as exc:  # noqa: BLE001
        STATE["warnings"].append(f"sys.path hardening failed: {exc}")


def _load_dotenv() -> None:
    try:
        from .dotenv import load_default_files

        STATE["dotenv"] = load_default_files()
    except Exception as exc:  # noqa: BLE001 - .env loading must never break startup
        STATE["warnings"].append(f".env load failed: {exc}")


def install() -> dict[str, Any]:
    """Idempotently apply the bootstrap and return :data:`STATE`."""
    if getattr(sys, "_pf_agent_bootstrapped", False):
        STATE["already_installed"] = True
        return STATE

    STATE["already_installed"] = False
    STATE["warnings"] = []
    try:
        _configure_utf8_env()
        _reconfigure_stream("stdout", "stdout_reconfigured")
        _reconfigure_stream("stderr", "stderr_reconfigured")
        _reconfigure_stream("stdin", "stdin_reconfigured")
        _harden_sys_path()
        _load_dotenv()
    except Exception as exc:  # noqa: BLE001 - defense in depth
        STATE["warnings"].append(f"bootstrap error: {exc}")

    sys._pf_agent_bootstrapped = True  # type: ignore[attr-defined]
    return STATE


# Apply automatically on import so entry points only need `import _bootstrap`.
install()


__all__ = ["STATE", "install"]
