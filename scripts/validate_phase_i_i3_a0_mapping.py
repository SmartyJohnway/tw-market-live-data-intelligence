"""Validate reviewed probe mapping structure; UNRESOLVED is not semantic PASS."""
from __future__ import annotations
import hashlib
import sys
from pathlib import Path
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import run_phase_i_i3_a0_preflight as p


def validate():
    if not __debug__:
        raise RuntimeError("optimized_governance_validation_not_supported")
    with patch("socket.socket.connect", p.deny_network), patch("socket.create_connection", p.deny_network):
        mapping = p.load_mapping()
        assert hashlib.sha256((ROOT / p.RECORD).read_bytes()).hexdigest() == p.HISTORICAL_SHA
        tpex = mapping["markets"]["TPEX"]
        assert mapping["mapping_status"] == tpex["mapping_status"] == "UNRESOLVED"
        unresolved = tpex["unresolved_fields"]["dealer_total_sell"]
        assert unresolved["candidates"] == ["Dealers-TotalSell", "Dealers -TotalSell"]
        assert unresolved["selected"] is None and unresolved["reason"]
        assert tpex["required_common_core"]["dealer_total"]["sell_shares"] is None
        sell = tpex["required_common_core"][p.CORE[0]]["sell_shares"]
        assert sell == [" Foreign Investors include Mainland Area Investors (Foreign Dealers excluded)-Total Sell"]
        historical = __import__("json").loads((ROOT / p.RECORD).read_text(encoding="utf-8"))
        # Every resolved source key is in Attempt 1 inventory, without trimming.
        for market, m in mapping["markets"].items():
            observed = historical["sources"][market]["fields"]
            assert m["code_field"] in observed
            if m["date_source"] == "row":
                assert m["date_field"] in observed
            for spec in m["required_common_core"].values():
                expressions = [spec] if isinstance(spec, list) else spec.values()
                for keys in expressions:
                    if keys is not None:
                        assert all(k in observed for k in keys)
            for spec in m["source_native_optional"].values():
                keys = [spec] if isinstance(spec, str) else [k for expr in spec.values() for k in expr]
                assert all(k in observed for k in keys)
        print("Mapping integrity PASS; semantic mapping UNRESOLVED; P0 cannot PASS; market GETs=0")
        return mapping


if __name__ == "__main__":
    validate()
