"""Execution environment abstractions."""

from .base import ExecutionCapabilities, ExecutionEnvironment, ExecutionResult, FakeExecutionEnvironment
from .docker import DockerExecutionBackend, DockerPlan
from .local import LocalExecutionBackend
from .singularity import SingularityExecutionBackend, SingularityPlan
from .ssh import SSHExecutionBackend, SSHPlan

__all__ = [
    "DockerExecutionBackend",
    "DockerPlan",
    "ExecutionCapabilities",
    "ExecutionEnvironment",
    "ExecutionResult",
    "FakeExecutionEnvironment",
    "LocalExecutionBackend",
    "SSHExecutionBackend",
    "SSHPlan",
    "SingularityExecutionBackend",
    "SingularityPlan",
]
