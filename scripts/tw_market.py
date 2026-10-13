"""Product-facing entry point: python -m scripts.tw_market <command>."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.tw_market_lifecycle import main

if __name__ == "__main__":
    raise SystemExit(main())
