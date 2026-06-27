"""Fake ProseForge project script for adapter tests.

Echoes the received action and arguments as JSON so tests can assert that the
adapter passes the command through and parses the JSON payload.
"""

import json
import sys

argv = sys.argv[1:]
print(
    json.dumps(
        {
            "status": "ok",
            "script": "nf_project",
            "action": argv[0] if argv else None,
            "argv": argv,
        }
    )
)
