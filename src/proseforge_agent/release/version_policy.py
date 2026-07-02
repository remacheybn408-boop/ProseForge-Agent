"""Version bump discipline + PyPI published-version lookup (Task 189).

``VersionPolicy`` computes the next release version and refuses to publish a
version already present on the target index. ``PyPIPublishedVersions`` reads
the target index's JSON API through an injectable ``fetch_json`` callable so
tests stay offline. On a fetch error the lookup fails open (returns an empty
set) rather than blocking a release on a transient network issue.
"""

from __future__ import annotations

import json as _json
import re
import urllib.request
from collections.abc import Callable
from typing import Any

from ..errors import ConfigurationError


_RELEASE_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:(rc|a|b)(\d+))?$")

_INDEX_URLS = {
    "testpypi": "https://test.pypi.org/pypi/proseforge-agent/json",
    "pypi": "https://pypi.org/pypi/proseforge-agent/json",
}


class VersionPolicy:
    """Compute the next version and guard against duplicate publishes."""

    def __init__(self, current: str) -> None:
        self.current = str(current).strip()

    def _parse(self) -> tuple[int, int, int, str, int]:
        match = _RELEASE_RE.match(self.current)
        if not match:
            raise ConfigurationError(
                f"malformed version {self.current!r}; expected MAJOR.MINOR.PATCH[rcN]"
            )
        major, minor, patch = int(match.group(1)), int(match.group(2)), int(match.group(3))
        pre_id = match.group(4) or ""
        pre_num = int(match.group(5)) if match.group(5) else 0
        return major, minor, patch, pre_id, pre_num

    def next(self, bump: str, *, pre_id: str = "rc") -> str:
        major, minor, patch, cur_pre, cur_pre_num = self._parse()
        if bump == "patch":
            return f"{major}.{minor}.{patch + 1}"
        if bump == "minor":
            return f"{major}.{minor + 1}.0"
        if bump == "major":
            return f"{major + 1}.0.0"
        if bump == "prerelease":
            if cur_pre == pre_id:
                # bump the existing prerelease counter on the same base version
                return f"{major}.{minor}.{patch}{pre_id}{cur_pre_num + 1}"
            # start a prerelease for the next patch
            return f"{major}.{minor}.{patch + 1}{pre_id}1"
        raise ConfigurationError(
            f"unknown bump kind {bump!r}; expected patch/minor/major/prerelease"
        )

    def refuse_duplicate(self, candidate: str, published: set[str]) -> None:
        if candidate in published:
            raise ConfigurationError(
                f"version {candidate} already published; bump before publishing"
            )


class PyPIPublishedVersions:
    """Read the set of already-published versions from a PyPI-like JSON index."""

    def __init__(self, *, fetch_json: Callable[[str], dict[str, Any]] | None = None) -> None:
        self._fetch_json = fetch_json or _default_fetch_json

    def for_repository(self, repository: str) -> set[str]:
        url = _INDEX_URLS.get(repository)
        if url is None:
            raise ConfigurationError(
                f"unknown repository {repository!r}; expected one of {tuple(_INDEX_URLS)}"
            )
        try:
            payload = self._fetch_json(url)
        except Exception:  # noqa: BLE001 - fail open: a fetch error must not block release
            return set()
        releases = payload.get("releases") if isinstance(payload, dict) else None
        if not isinstance(releases, dict):
            return set()
        return {str(version) for version in releases}


def _default_fetch_json(url: str) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=10) as resp:  # noqa: S310 - trusted PyPI host
        return _json.loads(resp.read().decode("utf-8"))


__all__ = ["PyPIPublishedVersions", "VersionPolicy"]
