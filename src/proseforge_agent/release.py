"""Release gate for the first usable Agent spine.

The release check fails unless the core guarantees hold: the fake provider is
deterministically certifiable, the memory store enforces its source-required
audit, the operator and developer docs ship their examples, and the offline
fake demo runs end to end. Any missing pillar blocks release.
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from .errors import MemoryError, ProseForgeAgentError
from .memory.store import MemoryItem, MemoryStore


class ReleaseError(ProseForgeAgentError):
    """Raised when a release check cannot be evaluated."""


@dataclass
class CheckResult:
    """The outcome of one release check."""

    name: str
    passed: bool
    detail: str = ""


@dataclass
class ReleaseReport:
    """Aggregate release readiness."""

    passed: bool
    checks: list[CheckResult] = field(default_factory=list)

    def render(self) -> str:
        lines = [f"# Release Check — {'PASS' if self.passed else 'FAIL'}", ""]
        for check in self.checks:
            mark = "ok" if check.passed else "FAIL"
            lines.append(f"- [{mark}] {check.name}: {check.detail}")
        return "\n".join(lines) + "\n"


class ReleaseChecker:
    """Evaluate the release gate against a repository root."""

    def __init__(self, repo_root: str | Path) -> None:
        self._repo_root = Path(repo_root)

    def run(self) -> ReleaseReport:
        checks = [
            self.check_provider_certification(),
            self.check_memory_audit(),
            self.check_docs_examples(),
            self.check_fake_demo(),
        ]
        return ReleaseReport(passed=all(c.passed for c in checks), checks=checks)

    # -- individual checks ----------------------------------------------

    def check_provider_certification(self) -> CheckResult:
        from .llm.base import Message, ProviderRequest
        from .llm.registry import ProviderRegistry

        registry = ProviderRegistry.from_dict(
            {
                "providers": [{"name": "fake", "kind": "fake", "model": "fake-1"}],
                "roles": {},
                "default_provider": "fake",
            }
        )
        provider = registry.provider_for_role("drafter")
        request = ProviderRequest(
            role="drafter", messages=[Message(role="user", content="certify")]
        )
        deterministic = provider.generate(request).text == provider.generate(request).text
        return CheckResult(
            name="provider_certification",
            passed=deterministic,
            detail="fake provider deterministic" if deterministic else "non-deterministic",
        )

    def check_memory_audit(self) -> CheckResult:
        with tempfile.TemporaryDirectory() as tmp:
            store = MemoryStore(Path(tmp) / "audit.db")
            enforced = False
            try:
                store.add(
                    MemoryItem(
                        project_slug="rel", type="canon_fact", text="fact", source="bible"
                    )
                )
                try:
                    store.add(
                        MemoryItem(project_slug="rel", type="canon_fact", text="x", source="")
                    )
                except MemoryError:
                    enforced = True
            finally:
                store.close()
        return CheckResult(
            name="memory_audit",
            passed=enforced,
            detail="source requirement enforced" if enforced else "audit not enforced",
        )

    def check_docs_examples(self) -> CheckResult:
        operator = self._repo_root / "docs" / "operator-quickstart.md"
        developer = self._repo_root / "docs" / "developer-extensions.md"
        ok = (
            operator.is_file()
            and developer.is_file()
            and "PROSEFORGE_ROOT" in operator.read_text(encoding="utf-8")
        )
        return CheckResult(
            name="docs_examples",
            passed=ok,
            detail="operator/developer docs present" if ok else "docs or examples missing",
        )

    def check_fake_demo(self) -> CheckResult:
        from .demo import DemoRunner

        with tempfile.TemporaryDirectory() as tmp:
            try:
                result = DemoRunner(tmp).run(provider="fake")
                ok = result.status == "ok" and result.report_pack.exists()
                detail = "demo produced report pack" if ok else "demo incomplete"
            except ProseForgeAgentError as exc:
                ok, detail = False, f"demo failed: {exc}"
        return CheckResult(name="fake_demo", passed=ok, detail=detail)


__all__ = ["ReleaseError", "CheckResult", "ReleaseReport", "ReleaseChecker"]
