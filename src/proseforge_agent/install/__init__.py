"""Installation, onboarding, and native-platform helpers."""

from .first_run import FirstRunResult, FirstRunWizard
from .app_dirs import AppDirs
from .binary_packaging import BinaryManifest, ManifestReport
from .doctor import DoctorCheck, DoctorReport, InstallationDoctor
from .platform_io import ShellCommandRenderer, TerminalCaps, read_text_utf8, write_text_utf8
from .package_checks import PackageCheck, PackageChecker, PackageReport
from .provider_setup import ProviderSetupResult, ProviderSetupWizard
from .secrets import SecretLookup, SecretStore
from .windows import WindowsChecks
from .macos import MacOSChecks
from .linux import LinuxChecks

__all__ = [
    "AppDirs",
    "BinaryManifest",
    "DoctorCheck",
    "DoctorReport",
    "FirstRunResult",
    "FirstRunWizard",
    "InstallationDoctor",
    "LinuxChecks",
    "MacOSChecks",
    "ManifestReport",
    "PackageCheck",
    "PackageChecker",
    "PackageReport",
    "ProviderSetupResult",
    "ProviderSetupWizard",
    "SecretLookup",
    "SecretStore",
    "ShellCommandRenderer",
    "TerminalCaps",
    "WindowsChecks",
    "read_text_utf8",
    "write_text_utf8",
]
