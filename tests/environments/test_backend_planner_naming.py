"""Planning backends are named ``*BackendPlanner`` not ``*ExecutionBackend`` (finding 4.3).

The five remote/container backends only emit a ``*Plan`` from ``check()`` and
never execute a command, so their names must not masquerade as executors. The
local backend is a real executor (``run()``) and keeps its name.
"""

from __future__ import annotations

import proseforge_agent.environments as environments
from proseforge_agent.environments import (
    DaytonaBackendPlanner,
    DockerBackendPlanner,
    LocalExecutionBackend,
    ModalBackendPlanner,
    SingularityBackendPlanner,
    SSHBackendPlanner,
)

PLANNERS = [
    DockerBackendPlanner,
    SSHBackendPlanner,
    SingularityBackendPlanner,
    ModalBackendPlanner,
    DaytonaBackendPlanner,
]

OLD_NAMES = [
    "DockerExecutionBackend",
    "SSHExecutionBackend",
    "SingularityExecutionBackend",
    "ModalExecutionBackend",
    "DaytonaExecutionBackend",
]


def test_planners_expose_check_and_never_run():
    for planner in PLANNERS:
        assert hasattr(planner, "check"), f"{planner.__name__} must expose check()"
        assert not hasattr(planner, "run"), f"{planner.__name__} is a planner and must not expose run()"


def test_local_backend_remains_a_real_executor():
    assert hasattr(LocalExecutionBackend, "run")
    assert not hasattr(LocalExecutionBackend, "check")


def test_misleading_execution_backend_names_are_gone():
    for old in OLD_NAMES:
        assert not hasattr(environments, old), f"{old} still exported; rename incomplete"
        assert old not in environments.__all__
