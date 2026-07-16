#!/usr/bin/env python3
"""Shared deterministic utilities for Taiwan security-master scripts."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from datetime import date
from typing import Any


ISO_DATE_RE = re.compile(r"^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})$")
ROC_DATE_RE = re.compile(r"^(\d{2,3})(?:年|[-/.]?)(\d{1,2})(?:月|[-/.]?)(\d{1,2})(?:日)?$")


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    return " ".join(text.replace("\u3000", " ").split()).strip()


def normalize_name(value: Any) -> str:
    text = normalize_text(value).casefold()
    return re.sub(r"[\s\-_.·,，()（）'\"]+", "", text)


def normalize_date(value: Any) -> str | None:
    """Normalize Gregorian or ROC dates to ISO; return None for unknown input."""
    raw = normalize_text(value)
    if not raw or raw.lower() in {"unknown", "n/a", "na", "null", "none", "-", "－"}:
        return None

    compact = re.sub(r"\s+", "", raw)
    if compact.isdigit() and len(compact) == 8 and int(compact[:4]) >= 1900:
        year, month, day = int(compact[:4]), int(compact[4:6]), int(compact[6:8])
    elif compact.isdigit() and len(compact) == 7:
        year, month, day = int(compact[:3]) + 1911, int(compact[3:5]), int(compact[5:7])
    else:
        match = ISO_DATE_RE.match(compact)
        if match:
            year, month, day = map(int, match.groups())
        else:
            match = ROC_DATE_RE.match(compact)
            if not match:
                return None
            roc_year, month, day = map(int, match.groups())
            year = roc_year + 1911

    try:
        return date(year, month, day).isoformat()
    except ValueError:
        return None


def isin_checksum_valid(value: Any) -> bool:
    """Validate an ISO 6166 ISIN using the Luhn checksum."""
    isin = normalize_text(value).upper().replace(" ", "")
    if not re.fullmatch(r"[A-Z]{2}[A-Z0-9]{9}[0-9]", isin):
        return False
    expanded = "".join(str(ord(ch) - 55) if ch.isalpha() else ch for ch in isin)
    total = 0
    parity = len(expanded) % 2
    for index, char in enumerate(expanded):
        digit = int(char)
        if index % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def file_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
