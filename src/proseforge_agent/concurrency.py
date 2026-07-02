"""Cross-platform advisory locking and SQLite busy-retry primitives.

Once chat, background jobs, and the local API can run at the same time, the
agent database and workflow state need protection from concurrent writers.
This module provides one shared locking primitive used by both stores:

* :class:`FileLock` — a cross-platform advisory file lock (``fcntl`` on POSIX,
  ``msvcrt`` on Windows) with a bounded acquisition timeout and a
  context-manager form. Writers contending for the same lock serialize; a writer
  that cannot acquire within the timeout fails cleanly instead of corrupting data.
* :func:`with_sqlite_retry` — retries an operation on ``database is locked``
  within a bounded budget.

It is a low-level utility with no provider, workflow, or chat logic; the stores
acquire a lock around their own write paths.
"""

from __future__ import annotations

import os
import sqlite3
import time
import warnings
from pathlib import Path
from typing import Callable, TypeVar

from .errors import ProseForgeAgentError

try:  # POSIX
    import fcntl

    _HAVE_FCNTL = True
except ImportError:  # pragma: no cover - platform dependent
    _HAVE_FCNTL = False

try:  # Windows
    import msvcrt

    _HAVE_MSVCRT = True
except ImportError:  # pragma: no cover - platform dependent
    _HAVE_MSVCRT = False

T = TypeVar("T")


class LockError(ProseForgeAgentError):
    """Raised when a file lock cannot be acquired within its timeout."""


class FileLock:
    """A cross-platform advisory file lock with a bounded acquisition timeout.

    The lock is tied to an open file descriptor, so the OS releases it if the
    holding process dies — a stale lock *file* left on disk is therefore still
    acquirable. UTF-8 names and spaces in the path are supported.
    """

    def __init__(self, path: str | Path, timeout: float = 10.0, poll_interval: float = 0.05) -> None:
        self.path = Path(path)
        self.timeout = timeout
        self.poll_interval = poll_interval
        self._fd: int | None = None
        # True when no OS lock primitive is available and the lock is advisory
        # in-name-only. Surfaced so callers/tests can detect the degraded mode
        # instead of it failing silently (finding 2.3).
        self.degraded = not (_HAVE_FCNTL or _HAVE_MSVCRT)

    def acquire(self) -> "FileLock":
        if self._fd is not None:
            return self  # already held by this instance
        if self.degraded:
            warnings.warn(
                "FileLock has no OS locking primitive (fcntl/msvcrt); writers are "
                "NOT serialized across processes on this platform",
                RuntimeWarning,
                stacklevel=2,
            )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(str(self.path), os.O_RDWR | os.O_CREAT, 0o644)
        deadline = time.monotonic() + self.timeout
        while True:
            try:
                self._lock_fd(fd)
                self._fd = fd
                return self
            except OSError:
                if time.monotonic() >= deadline:
                    os.close(fd)
                    raise LockError(
                        f"could not acquire lock {self.path} within {self.timeout}s"
                    )
                time.sleep(self.poll_interval)

    def release(self) -> None:
        if self._fd is None:
            return
        try:
            self._unlock_fd(self._fd)
        finally:
            os.close(self._fd)
            self._fd = None

    def __enter__(self) -> "FileLock":
        return self.acquire()

    def __exit__(self, *exc) -> None:
        self.release()

    @staticmethod
    def _lock_fd(fd: int) -> None:
        if _HAVE_FCNTL:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        elif _HAVE_MSVCRT:
            os.lseek(fd, 0, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        # If neither primitive is available the lock degrades to a no-op.

    @staticmethod
    def _unlock_fd(fd: int) -> None:
        if _HAVE_FCNTL:
            fcntl.flock(fd, fcntl.LOCK_UN)
        elif _HAVE_MSVCRT:
            os.lseek(fd, 0, os.SEEK_SET)
            try:
                msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
            except OSError:  # pragma: no cover - already unlocked
                pass


def with_sqlite_retry(
    operation: Callable[[], T],
    busy_timeout: float = 5.0,
    poll_interval: float = 0.05,
) -> T:
    """Run ``operation``, retrying on ``database is locked`` within a bound.

    Re-raises the original error once the budget is exhausted, or immediately for
    any other operational error.
    """
    deadline = time.monotonic() + busy_timeout
    busy_code = getattr(sqlite3, "SQLITE_BUSY", 5)
    while True:
        try:
            return operation()
        except sqlite3.OperationalError as exc:
            # Prefer the stable errorcode (Python 3.11+); fall back to the
            # message for older interpreters / drivers (finding 2.4).
            is_busy = getattr(exc, "sqlite_errorcode", None) == busy_code
            if not is_busy and "database is locked" not in str(exc).lower():
                raise
            if time.monotonic() >= deadline:
                raise
            time.sleep(poll_interval)


__all__ = ["FileLock", "LockError", "with_sqlite_retry"]
