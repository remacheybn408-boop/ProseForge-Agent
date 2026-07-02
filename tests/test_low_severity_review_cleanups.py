"""Low-severity core-review cleanups (findings 1.3, 2.3, 2.4, 3.4, 7.1)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from proseforge_agent import concurrency
from proseforge_agent.agent.sandbox import Approval, ExecRequest, Sandbox
from proseforge_agent.concurrency import FileLock, with_sqlite_retry

SRC = Path(__file__).resolve().parents[1] / "src" / "proseforge_agent"


class _Safety:
    def assess(self, content, provenance, session_ceiling):
        class V:
            is_flagged = False
            reason = "ok"

        return V()


# --- 1.3 sandbox distinguishes the two denial reasons ---------------------


def test_sandbox_ceiling_gate_reports_insufficient_permission(tmp_path):
    sandbox = Sandbox(permissions="read_only", safety=_Safety(), workspace_root=tmp_path)
    result = sandbox.run(ExecRequest(argv=["echo", "hi"], permission="engine_write"), approval=None)
    assert result.ok is False
    assert result.error == "insufficient_permission"


def test_sandbox_missing_approval_reports_approval_required(tmp_path):
    sandbox = Sandbox(permissions="engine_write", safety=_Safety(), workspace_root=tmp_path)
    result = sandbox.run(ExecRequest(argv=["echo", "hi"], permission="read_only"), approval=None)
    assert result.ok is False
    assert result.error == "approval_required"


# --- 2.3 FileLock no longer degrades silently -----------------------------


def test_filelock_warns_when_no_primitive_available(tmp_path, monkeypatch):
    monkeypatch.setattr(concurrency, "_HAVE_FCNTL", False)
    monkeypatch.setattr(concurrency, "_HAVE_MSVCRT", False)
    lock = FileLock(tmp_path / "x.lock")
    with pytest.warns(RuntimeWarning):
        with lock:
            pass
    assert lock.degraded is True


# --- 2.4 sqlite retry keys off SQLITE_BUSY errorcode ----------------------


def test_with_sqlite_retry_uses_busy_errorcode_not_only_message():
    calls = {"n": 0}

    def op():
        calls["n"] += 1
        if calls["n"] == 1:
            exc = sqlite3.OperationalError("locked up tight")  # message lacks canonical text
            exc.sqlite_errorcode = getattr(sqlite3, "SQLITE_BUSY", 5)
            raise exc
        return "ok"

    assert with_sqlite_retry(op, busy_timeout=1.0, poll_interval=0.0) == "ok"
    assert calls["n"] == 2


def test_with_sqlite_retry_reraises_non_busy_error():
    def op():
        raise sqlite3.OperationalError("no such table: widgets")

    with pytest.raises(sqlite3.OperationalError):
        with_sqlite_retry(op, busy_timeout=0.2, poll_interval=0.0)


# --- 3.4 _redact_argv renamed to _format_argv -----------------------------


def test_release_publish_format_argv_replaces_redact_argv():
    from proseforge_agent.release import publish

    assert hasattr(publish, "_format_argv")
    assert not hasattr(publish, "_redact_argv")
    assert publish._format_argv(["twine", "upload", "dist/*"]) == "twine upload dist/*"


# --- 7.1 future annotations on the two flagged modules --------------------


@pytest.mark.parametrize("rel", ["agent/modes.py", "errors.py"])
def test_module_has_future_annotations(rel):
    text = (SRC / rel).read_text(encoding="utf-8")
    assert "from __future__ import annotations" in text
