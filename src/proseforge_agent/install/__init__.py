"""Installation, onboarding, and native-platform helpers."""

from .first_run import FirstRunResult, FirstRunWizard
from .app_dirs import AppDirs
from .doctor import DoctorCheck, DoctorReport, InstallationDoctor
from .platform_io import ShellCommandRenderer, TerminalCaps, read_text_utf8, write_text_utf8

__all__ = [
    "AppDirs",
    "DoctorCheck",
    "DoctorReport",
    "FirstRunResult",
    "FirstRunWizard",
    "InstallationDoctor",
    "ShellCommandRenderer",
    "TerminalCaps",
    "read_text_utf8",
    "write_text_utf8",
]
