"""Windows UTF-8 early bootstrap tests (Task 190)."""

from __future__ import annotations

import importlib
import os
import sys


def _reload_bootstrap():
    from proseforge_agent import _bootstrap

    sys._pf_agent_bootstrapped = False
    return importlib.reload(_bootstrap)


def test_bootstrap_sets_python_utf8_and_reconfigures_streams(monkeypatch):
    monkeypatch.delenv("PYTHONUTF8", raising=False)
    monkeypatch.delenv("PYTHONIOENCODING", raising=False)

    bootstrap = _reload_bootstrap()

    assert os.environ["PYTHONUTF8"] == "1"
    assert os.environ["PYTHONIOENCODING"].lower().startswith("utf-8")
    assert bootstrap.STATE["stdout_reconfigured"] in (True, "not_a_text_wrapper", False)


def test_bootstrap_records_preexisting_python_utf8(monkeypatch):
    monkeypatch.setenv("PYTHONUTF8", "1")

    bootstrap = _reload_bootstrap()

    assert bootstrap.STATE["python_utf8_set"] == "preexisting"


def test_bootstrap_is_idempotent():
    bootstrap = _reload_bootstrap()
    first = dict(bootstrap.STATE)
    assert first["already_installed"] is False

    second = bootstrap.install()
    assert second["already_installed"] is True


def test_bootstrap_hardens_syspath():
    bootstrap = _reload_bootstrap()
    assert "" not in sys.path
    assert "." not in sys.path
    assert bootstrap.STATE["sys_path_hardened"] is True


def test_bootstrap_never_raises_on_missing_streams(monkeypatch):
    class _NoReconfigure:
        def write(self, *_):
            return 0

    monkeypatch.setattr(sys, "stdout", _NoReconfigure())
    monkeypatch.setattr(sys, "stderr", _NoReconfigure())

    bootstrap = _reload_bootstrap()  # must not raise

    assert bootstrap.STATE["stdout_reconfigured"] == "not_a_text_wrapper"


def test_bootstrap_install_is_importable_and_returns_state():
    from proseforge_agent import _bootstrap

    state = _bootstrap.install()
    assert isinstance(state, dict)
    assert "warnings" in state


def test_main_module_exposes_cli_main():
    from proseforge_agent import __main__

    assert callable(__main__.main)


def test_cli_still_works_after_bootstrap():
    from proseforge_agent.cli import main

    assert main(["--version"]) == 0


def test_entry_points_import_bootstrap_first():
    # The three interactive entry points must import _bootstrap so UTF-8 is
    # configured before any user-facing output.
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "src" / "proseforge_agent"
    for rel in ("cli.py", "chat/repl.py", "demo.py"):
        text = (root / rel).read_text(encoding="utf-8")
        assert "_bootstrap" in text, f"{rel} must import _bootstrap"
