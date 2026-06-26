from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "docs/protocol/TWSE_MIS_PROTOCOL.md"
FIELD_DICT = ROOT / "docs/protocol/TWSE_MIS_FIELD_DICTIONARY.md"
CONTRACT = ROOT / "docs/contracts/twse_mis_normalized_snapshot_v2_draft.md"


def read(path):
    return path.read_text(encoding="utf-8").lower()


def test_docs_exist():
    assert PROTOCOL.exists()
    assert FIELD_DICT.exists()
    assert CONTRACT.exists()


def test_docs_mention_governance_boundaries():
    combined = "\n".join(read(p) for p in [PROTOCOL, FIELD_DICT, CONTRACT])
    for phrase in [
        "unofficial", "fragile", "no official realtime guarantee", "not production current market state",
        "not be used as a trading signal", "no full-market scan", "no production refresh",
    ]:
        assert phrase in combined


def test_field_dictionary_contains_required_fields_and_flags():
    content = read(FIELD_DICT)
    for field in ["c", "n", "ex", "ch", "z", "y", "o", "h", "l", "v", "tv", "a", "f", "b", "g", "u", "w", "d", "t", "tlong", "querytime", "userdelay", "cachedalive"]:
        assert f"`{field}`" in content
    assert "data_quality_flags" in content
    assert "source_risk_flags" in content
    assert "unofficial_source_risk" in content
    assert "unknown_or_unverified_semantics" in content


def test_contract_contains_v2_fields():
    content = read(CONTRACT)
    for field in ["source_id", "source_authority", "source_risk_flags", "symbol", "exchange", "instrument_type", "name", "price", "open", "high", "low", "previous_close", "volume", "bid_ladder", "ask_ladder", "source_date", "source_time", "source_timestamp", "retrieved_at", "staleness_seconds", "delay_status", "freshness_status", "price_semantics", "raw_fields_present", "data_quality_flags", "normalization_version", "normalization_status", "errors"]:
        assert f"`{field}`" in content


def test_no_claims_of_official_realtime():
    combined = "\n".join(read(p) for p in [PROTOCOL, FIELD_DICT, CONTRACT])
    forbidden = ["is an official api", "official realtime guarantee applies", "is realtime-guaranteed"]
    for phrase in forbidden:
        assert phrase not in combined
