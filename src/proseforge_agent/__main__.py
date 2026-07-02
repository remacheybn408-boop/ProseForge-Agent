"""``python -m proseforge_agent`` entry point (Task 190)."""

import proseforge_agent._bootstrap  # noqa: F401  # UTF-8 + path hardening, must be first

from proseforge_agent.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
