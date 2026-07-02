"""Docker image plan (Task 192).

A deterministic, in-code mirror of the checked-in ``Dockerfile`` so tests can
assert the layer sequence without building an image. Each step's command is a
fragment that must appear verbatim in the Dockerfile; the cross-check test
catches drift between this plan and the Dockerfile.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class DockerImagePlan:
    """Canonical ordered layers of the runtime image."""

    base_image: str
    user: str
    steps: list[tuple[str, str]] = field(default_factory=list)

    @classmethod
    def from_repo(cls, root: str | Path) -> "DockerImagePlan":
        # `root` is accepted for symmetry with other planners; the plan itself
        # is canonical and does not read or write the filesystem.
        return cls(
            base_image="python:3.11-slim-bookworm",
            user="pfagent",
            steps=[
                ("base", "FROM python:3.11-slim-bookworm"),
                ("system_deps", "apt-get install -y --no-install-recommends git ca-certificates"),
                ("create_user", "useradd --create-home --uid 1000 pfagent"),
                ("env", "PF_AGENT_WORKSPACE=/data"),
                ("copy_source", "COPY . /app"),
                ("install_package", "pip install --no-cache-dir proseforge-agent"),
                ("entrypoint_copy", "COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh"),
                ("data_volume", 'VOLUME ["/data"]'),
                ("expose", "EXPOSE 8765"),
                ("drop_privileges", "USER pfagent"),
                ("entrypoint", 'ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]'),
            ],
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "base_image": self.base_image,
            "user": self.user,
            "steps": [{"name": name, "command": command} for name, command in self.steps],
        }


__all__ = ["DockerImagePlan"]
