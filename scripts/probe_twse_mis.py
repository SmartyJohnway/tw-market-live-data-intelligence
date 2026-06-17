"""Experimental TWSE MIS probe.

This script is intentionally conservative. It first visits the official MIS page
in order to establish a normal browser-like session, then attempts a low-volume
request to candidate getStockInfo endpoints.

Do not run high-frequency polling. Respect source limitations and terms.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Iterable

import requests

BASE = "https://mis.twse.com.tw/stock"
INDEX_URL = f"{BASE}/index.jsp"
API_URL = f"{BASE}/api/getStockInfo.jsp"

DEFAULT_SYMBOLS = [
    "tse_t00.tw",   # TAIEX candidate
    "otc_o00.tw",   # TPEx candidate
    "tse_2330.tw",  # TSMC
    "tse_2454.tw",  # MediaTek
    "tse_2317.tw",  # Hon Hai
    "tse_2382.tw",  # Quanta
]


def probe(symbols: Iterable[str] = DEFAULT_SYMBOLS) -> dict:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (compatible; TW-Market-Live-Data-Research/0.1; +research)",
            "Accept": "application/json,text/plain,*/*",
            "Referer": INDEX_URL,
        }
    )

    # Establish session/cookies in a normal low-volume way.
    first = session.get(INDEX_URL, timeout=10)
    time.sleep(0.5)

    params = {
        "ex_ch": "|".join(symbols),
        "json": "1",
        "delay": "0",
        "_": str(int(time.time() * 1000)),
    }
    resp = session.get(API_URL, params=params, timeout=10)

    result = {
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "index_status_code": first.status_code,
        "api_status_code": resp.status_code,
        "api_url": resp.url,
        "cookies_present": bool(session.cookies),
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
