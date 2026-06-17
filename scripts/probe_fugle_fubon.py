from datetime import datetime, timezone
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from probe_utils import generate_standard_envelope

def probe():
    print("Documenting Fugle and Fubon feasibility...")

    probe_id_fugle = f"fugle_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    probe_id_fubon = f"fubon_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    res_fugle = generate_standard_envelope(
        probe_id=probe_id_fugle,
        source="Fugle_MarketData",
        source_type="commercial_api",
        contract_status="auth_required",
        http_status="N/A",
        url="https://developer.fugle.tw/",
        requires_auth=True,
        risk_level="low",
        risk_notes=["Requires personal API key"],
        ai_suitability="live_streaming_capable",
        warnings=["Not probed live due to missing configured credentials."]
    )

    res_fubon = generate_standard_envelope(
        probe_id=probe_id_fubon,
        source="Fubon_Neo_API",
        source_type="broker_api",
        contract_status="doc_only",
        http_status="N/A",
        url="https://developer.fubon.com/",
        requires_auth=True,
        risk_level="high",
        risk_notes=["Requires valid brokerage account", "Requires certificate setup"],
        ai_suitability="execution_capable_but_complex",
        warnings=["Not probed live. Complex auth requirements."]
    )

    return [res_fugle, res_fubon]

if __name__ == "__main__":
    import json
    print(json.dumps(probe(), indent=2, ensure_ascii=False))
