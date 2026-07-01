"""Developer-facing plugin test harness."""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

from .dependencies import PluginDependencyManager
from .hooks import PluginAPI, PluginHookRegistry, PluginHookResult
from .manifest import PluginManifest
from .permissions import PLUGIN_PERMISSIONS
from .sandbox import PluginSandbox, PluginSandboxPolicy


@dataclass(frozen=True)
class PluginTestReport:
    plugin_id: str
    status: str
    checks: dict[str, str]
    hook_result: PluginHookResult | None = None
    errors: list[str] = field(default_factory=list)
    demo_project_path: str = ""

    def to_dict(self) -> dict:
        data = asdict(self)
        data["hook_result"] = self.hook_result.to_dict() if self.hook_result else None
        return data


class PluginTestHarness:
    """Run deterministic validation checks against a local plugin directory."""

    def __init__(self, work_root: str | Path = ".pf-agent/plugin-test") -> None:
        self.work_root = Path(work_root)

    def run(
        self,
        plugin_path: str | Path,
        *,
        with_demo_project: bool = False,
        hook: str = "on_after_export",
    ) -> PluginTestReport:
        root = Path(plugin_path)
        checks: dict[str, str] = {}
        errors: list[str] = []
        hook_result: PluginHookResult | None = None
        plugin_id = str(root)

        try:
            manifest = PluginManifest.load(root / "plugin.yaml")
            plugin_id = manifest.id
            checks["manifest"] = "ok"
        except Exception as exc:  # noqa: BLE001 - harness reports all plugin failures.
            return PluginTestReport(plugin_id=plugin_id, status="blocked", checks={"manifest": "failed"}, errors=[str(exc)])

        dependency_report = PluginDependencyManager(self.work_root).check(root)
        checks["dependencies"] = "ok" if dependency_report.status == "ok" else "blocked"
        errors.extend(issue.message for issue in dependency_report.issues)

        unknown_permissions = sorted(set(manifest.permissions).difference(PLUGIN_PERMISSIONS))
        checks["permissions"] = "ok" if not unknown_permissions else "failed"
        if unknown_permissions:
            errors.append(f"unknown permissions: {', '.join(unknown_permissions)}")

        register_fn: Callable[[PluginAPI], Any] | None = None
        try:
            module, register_fn = self._load_entrypoint(root, manifest.entrypoint)
            checks["import"] = "ok" if isinstance(module, ModuleType) else "failed"
        except Exception as exc:  # noqa: BLE001
            checks["import"] = "failed"
            errors.append(str(exc))

        registry = PluginHookRegistry()
        if register_fn is not None:
            try:
                register_fn(PluginAPI(hooks=registry))
                checks["register"] = "ok"
            except Exception as exc:  # noqa: BLE001
                checks["register"] = "failed"
                errors.append(str(exc))
        else:
            checks["register"] = "skipped"

        if checks.get("register") == "ok":
            try:
                hook_result = registry.emit(hook, {"plugin_id": manifest.id})
                checks["hooks"] = "ok" if hook_result.status in {"ok", "partial"} else "failed"
                errors.extend(error.error for error in hook_result.errors)
            except Exception as exc:  # noqa: BLE001
                checks["hooks"] = "failed"
                errors.append(str(exc))
        else:
            checks["hooks"] = "skipped"

        demo_project = self._demo_project(with_demo_project)
        sandbox = PluginSandbox(PluginSandboxPolicy(project_root=demo_project))
        checks["sandbox"] = "ok" if sandbox.api.read_file("../outside.txt") is None else "failed"
        if checks["sandbox"] != "ok":
            errors.append("sandbox allowed file access outside the demo project")

        status = "ok" if all(value == "ok" for value in checks.values()) else "blocked"
        return PluginTestReport(
            plugin_id=manifest.id,
            status=status,
            checks=checks,
            hook_result=hook_result,
            errors=errors,
            demo_project_path=str(demo_project),
        )

    def _demo_project(self, with_demo_project: bool) -> Path:
        project = self.work_root / ("demo-project" if with_demo_project else "empty-project")
        project.mkdir(parents=True, exist_ok=True)
        return project

    @staticmethod
    def _load_entrypoint(plugin_path: Path, entrypoint: str) -> tuple[ModuleType, Callable[[PluginAPI], Any]]:
        if ":" not in entrypoint:
            raise ValueError("plugin entrypoint must be '<module>:<callable>'")
        module_name, callable_name = entrypoint.split(":", 1)
        module_path = plugin_path / (module_name.replace(".", "/") + ".py")
        if not module_path.exists():
            package_path = plugin_path / module_name.replace(".", "/") / "__init__.py"
            module_path = package_path
        if not module_path.exists():
            raise FileNotFoundError(f"plugin entrypoint module not found: {module_name}")

        unique_name = f"_pf_plugin_{abs(hash((str(module_path), entrypoint)))}"
        spec = importlib.util.spec_from_file_location(unique_name, module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load plugin module: {module_name}")
        module = importlib.util.module_from_spec(spec)
        sys.path.insert(0, str(plugin_path))
        try:
            spec.loader.exec_module(module)
        finally:
            try:
                sys.path.remove(str(plugin_path))
            except ValueError:
                pass
        register = getattr(module, callable_name)
        return module, register


__all__ = ["PluginTestHarness", "PluginTestReport"]
