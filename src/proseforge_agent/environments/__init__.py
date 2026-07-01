"""Execution environment abstractions."""

from .base import ExecutionCapabilities, ExecutionEnvironment, ExecutionResult, FakeExecutionEnvironment
from .checkpoints import EnvironmentCheckpoint
from .daytona import DaytonaExecutionBackend
from .docker import DockerExecutionBackend, DockerPlan
from .file_sync import FileSyncPlan, FileSyncPlanner
from .local import LocalExecutionBackend
from .modal import ModalExecutionBackend
from .process_registry import FakeProcessBackend, ProcessEntry, ProcessReadResult, ProcessRegistry
from .serverless import SERVERLESS_STATES, ServerlessPlan
from .singularity import SingularityExecutionBackend, SingularityPlan
from .ssh import SSHExecutionBackend, SSHPlan

__all__ = [
    "DaytonaExecutionBackend",
    "DockerExecutionBackend",
    "DockerPlan",
    "EnvironmentCheckpoint",
    "ExecutionCapabilities",
    "ExecutionEnvironment",
    "ExecutionResult",
    "FakeExecutionEnvironment",
    "FakeProcessBackend",
    "FileSyncPlan",
    "FileSyncPlanner",
    "LocalExecutionBackend",
    "ModalExecutionBackend",
    "ProcessEntry",
    "ProcessReadResult",
    "ProcessRegistry",
    "SSHExecutionBackend",
    "SSHPlan",
    "SERVERLESS_STATES",
    "ServerlessPlan",
    "SingularityExecutionBackend",
    "SingularityPlan",
]
