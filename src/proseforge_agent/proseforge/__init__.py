"""ProseForge engine integration.

The engine is reached only through :class:`ProseForgeAdapter`; nothing in this
package imports workflow, planning, or report logic (dependency direction is
one-way into the engine).
"""

from .adapter import ProseForgeAdapter
from .results import EngineActionResult, EngineDiscovery

__all__ = ["ProseForgeAdapter", "EngineActionResult", "EngineDiscovery"]
