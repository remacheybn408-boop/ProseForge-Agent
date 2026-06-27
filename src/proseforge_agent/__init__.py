"""ProseForge Agent package.

Importing this package must not read configuration, touch the filesystem,
or require API keys. Subsystem behavior lives behind dedicated submodules
that are imported explicitly by their callers.
"""

__version__ = "0.1.0"

__all__ = ["__version__"]
