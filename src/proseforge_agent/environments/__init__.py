"""Execution environment abstractions."""

from .base import ExecutionCapabilities, ExecutionEnvironment, ExecutionResult, FakeExecutionEnvironment
from .docker import DockerExecutionBackend, DockerPlan
from .local import LocalExecutionBackend

__all__ = [
    "DockerExecutionBackend",
    "DockerPlan",
    "ExecutionCapabilities",
    "ExecutionEnvironment",
    "ExecutionResult",
    "FakeExecutionEnvironment",
    "LocalExecutionBackend",
]
