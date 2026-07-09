from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.m5k_common import DEFAULT_WATCHLIST_PATH, build_conversation_context, conversation_context_markdown, dump_json, load_json, read_latest_observation

OUT_DIR = REPO_ROOT / "research/live_observation_runs/current_conversation_context"


def build_package(
    watchlist_path: Path = DEFAULT_WATCHLIST_PATH,
    out_dir: Path = OUT_DIR,
    *,
    now_utc: str | datetime | None = None,
    holiday_schedule_records: list[dict[str, object]] | None = None,
) -> dict:
    watchlist = load_json(watchlist_path)
    latest = read_latest_observation()
    context = build_conversation_context(watchlist, latest, now_utc=now_utc, holiday_schedule_records=holiday_schedule_records)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "conversation_context.json").write_text(dump_json(context), encoding="utf-8")
    (out_dir / "conversation_context.md").write_text(conversation_context_markdown(context), encoding="utf-8")
    return {"status": "ok", "output_dir": out_dir.relative_to(REPO_ROOT).as_posix(), "files": ["conversation_context.json", "conversation_context.md"], "context": context}


def main() -> int:
    ap = argparse.ArgumentParser(description="Build the M5N temporary AI conversation context package without network calls.")
    ap.add_argument("--watchlist", default=str(DEFAULT_WATCHLIST_PATH))
    ap.add_argument("--out-dir", default=str(OUT_DIR))
    args = ap.parse_args()
    result = build_package(Path(args.watchlist), Path(args.out_dir))
    print(dump_json({k: v for k, v in result.items() if k != "context"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
