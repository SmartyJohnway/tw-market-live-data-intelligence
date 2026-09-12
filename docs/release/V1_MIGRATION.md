# v0.1 to V1 migration

V1 retains historical M5/M8 artifacts for audit but moves the current operator
path to the installation-local Security Master, Unified Request flow, and
Persistent Watchlists.

1. Back up or export any local Watchlist state before changing installations.
2. Install the exact RC dependency set and run `python scripts/verify_environment.py`.
3. Run `python scripts/manage_security_master.py status`. `NOT_INITIALIZED` is
   valid for a new installation; initialization is an explicit operator action.
4. Start the current loopback workbench and Unified MCP. Use `/workbench/`, not
   a historical Mode-A browser route.
5. Continue to treat old M5/M8 reports as historical evidence. They are not
   automatically rewritten, promoted, or used as a hidden runtime fallback.

No database migration runs at import time, startup, or MCP launch. A future
release that changes a persisted Watchlist schema must provide an explicit,
tested migration and rollback path.
