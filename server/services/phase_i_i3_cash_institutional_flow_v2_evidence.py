"""Version-specific production V2 evidence validation; historical V1 is untouched."""
from __future__ import annotations

import json
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from .phase_i_i3_cash_institutional_flow_adapters import ROOT


def validate_evidence_v2(evidence: dict[str, Any]) -> None:
    """Validate production V2 schema and cross-field provenance semantics."""
    schema = json.loads((ROOT / "schemas/cash_institutional_flow_context_evidence.v2.schema.json").read_text(encoding="utf-8"))
    errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(evidence))
    if errors:
        raise ValueError("i3_v2_evidence_schema_invalid:" + errors[0].message)
    if evidence.get("schema_version") != "cash_institutional_flow_context_evidence.v2":
        raise ValueError("i3_v2_evidence_version_invalid")
    source = evidence.get("source")
    if not isinstance(source, dict) or source.get("source_reported_trade_date") != evidence.get("source_reported_trade_date"):
        raise ValueError("i3_v2_source_date_lineage_mismatch")
    if evidence.get("status") == "complete":
        if evidence.get("canonical_target_id") != f"{evidence.get('market')}:{evidence.get('security_code')}":
            raise ValueError("i3_v2_target_identity_mismatch")
        if evidence.get("trade_date") != evidence.get("source_reported_trade_date"):
            raise ValueError("i3_v2_trade_date_lineage_mismatch")
        if evidence.get("market") == "TWSE" and evidence.get("resolved_source_trade_date") != evidence.get("source_reported_trade_date"):
            raise ValueError("i3_v2_twse_bound_date_mismatch")
        if evidence.get("market") == "TPEX" and evidence.get("resolved_source_trade_date") is not None:
            raise ValueError("i3_v2_tpex_must_not_fabricate_resolved_query_date")
        groups = ("foreign_and_mainland_excluding_foreign_dealer", "investment_trust", "dealer_total")
        for name in groups:
            flow = evidence[name]
            if flow["net_shares"] != flow["buy_shares"] - flow["sell_shares"]:
                raise ValueError("i3_v2_flow_arithmetic_mismatch")
        if evidence["institutional_total_net_shares"] != sum(evidence[name]["net_shares"] for name in groups):
            raise ValueError("i3_v2_institutional_total_mismatch")
        for flow in evidence.get("source_native_optional", {}).values():
            if isinstance(flow, dict) and "buy_shares" in flow and flow["net_shares"] != flow["buy_shares"] - flow["sell_shares"]:
                raise ValueError("i3_v2_optional_flow_arithmetic_mismatch")
