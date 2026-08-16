"""``python -m aegis_sentinel.mcp_server`` — stdio server launcher."""

import sys

from aegis_sentinel.mcp_server.server import main

if __name__ == "__main__":
    sys.exit(main())
