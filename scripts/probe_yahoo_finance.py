"""Experimental Yahoo Finance probe for Taiwan symbols.

Yahoo endpoints are not treated as stable official APIs. Use only for research
and document failures clearly.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import requests

SYMBOLS = ["^TWII", "2330.TW", "2454.TW", "2317.TW", "2382.TW"]


def probe(symbols: list[str] = SYMBOLS) -> dict:
    url = "https://query1.finance.yahoo.com/v7/finance/quote"
    params = {"symbols": ",".join(symbols)}
    headers = {"User-Agent": "Mozilla/5.0 (compatible; TW-Market-Live-Data-Research/0.1)"}
    resp = requests.get(url, params=params, headers=headers, timeout=10)
    result = {
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "status_code": resp.status_code,
        "url": resp.url,
        "content_type": resp.headers.get("content-type"),
        "text_sample": resp.text[:1000],
    }
    try:
        result["json"] = resp.json()
    except Exception as exc:  # noqa: BLE001
        result["json_error"] = repr(exc)
    return result


if __name__ == "__main__":
    print(json.dumps(probe(), ensure_ascii=False, indent=2))
