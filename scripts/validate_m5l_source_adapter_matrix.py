#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.m5k_common import dump_json, load_source_adapter_matrix, validate_source_adapter_matrix

if __name__ == "__main__":
    result = validate_source_adapter_matrix(load_source_adapter_matrix())
    print(dump_json(result))
    raise SystemExit(0 if result["valid"] else 2)
