"""Docker and compose distribution tests (Task 192).

Planner-style: these assert the checked-in Dockerfile / compose / entrypoint
content. The image is only built when PF_AGENT_BUILD_DOCKER=1 (not in CI).
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from proseforge_agent.install.docker_plan import DockerImagePlan


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def test_dockerfile_uses_python_311_slim_and_non_root_user():
    dockerfile = _read("Dockerfile")
    assert "python:3.11-slim" in dockerfile
    assert "USER pfagent" in dockerfile
    assert "ENTRYPOINT" in dockerfile


def test_dockerignore_excludes_git_venv_and_pytest_cache():
    ignore = _read(".dockerignore")
    for pattern in (".git", ".venv", ".pytest_cache", "__pycache__", ".env"):
        assert pattern in ignore, f".dockerignore missing {pattern}"


def test_compose_linux_declares_service_and_workspace_volume():
    compose = yaml.safe_load(_read("docker-compose.yml"))
    services = compose["services"]
    assert "pf-agent" in services
    svc = services["pf-agent"]
    assert svc.get("image") == "proseforge-agent:latest"
    mounts = " ".join(svc.get("volumes", []))
    assert "/data" in mounts


def test_compose_windows_uses_named_volume_for_workspace():
    compose = yaml.safe_load(_read("docker-compose.windows.yml"))
    svc = compose["services"]["pf-agent"]
    volumes_top = compose.get("volumes", {})
    # a named volume must be declared and mounted at /data
    assert volumes_top, "windows compose must declare a named volume"
    mounts = " ".join(svc.get("volumes", []))
    assert "/data" in mounts
    named = list(volumes_top.keys())[0]
    assert named in mounts


def test_windows_compose_sets_pythonutf8_env():
    compose = yaml.safe_load(_read("docker-compose.windows.yml"))
    env = compose["services"]["pf-agent"].get("environment", {})
    env_text = env if isinstance(env, str) else " ".join(
        f"{k}={v}" for k, v in (env.items() if isinstance(env, dict) else [])
    ) + " ".join(env if isinstance(env, list) else [])
    assert "PYTHONUTF8" in str(env)


def test_compose_files_declare_service_port_from_env():
    for name in ("docker-compose.yml", "docker-compose.windows.yml"):
        compose = yaml.safe_load(_read(name))
        ports = " ".join(str(p) for p in compose["services"]["pf-agent"].get("ports", []))
        assert "8765" in ports
        assert "PF_AGENT_SERVICE_PORT" in ports


def test_entrypoint_passes_args_through_to_pf_agent():
    entry = _read("docker/entrypoint.sh")
    assert "pf-agent" in entry
    assert '"$@"' in entry


def test_docker_image_plan_steps_match_dockerfile():
    plan = DockerImagePlan.from_repo(REPO_ROOT)
    dockerfile = _read("Dockerfile")
    assert plan.base_image == "python:3.11-slim-bookworm"
    assert plan.user == "pfagent"
    assert plan.steps, "plan must have steps"
    for _name, command in plan.steps:
        assert command in dockerfile, f"plan step not reflected in Dockerfile: {command}"


def test_docker_plan_is_pure(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    DockerImagePlan.from_repo(REPO_ROOT)
    assert list(tmp_path.iterdir()) == []
