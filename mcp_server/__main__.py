from __future__ import annotations

import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    stream=sys.stderr,
)

try:
    from mcp_server.server import run
    run()
except KeyboardInterrupt:
    pass
