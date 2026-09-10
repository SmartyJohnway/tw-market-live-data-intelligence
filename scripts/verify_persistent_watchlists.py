"""Offline integrity verifier for the installation-local M8R-09 watchlist DB."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.m8r_09_persistent_watchlists import PersistentWatchlistStore, WatchlistError


def main() -> int:
    try:
        result = PersistentWatchlistStore().verify_integrity()
    except WatchlistError as exc:
        print(json.dumps({"status": "FAIL", "reason_code": exc.code, "details": exc.details}, ensure_ascii=False, sort_keys=True))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
