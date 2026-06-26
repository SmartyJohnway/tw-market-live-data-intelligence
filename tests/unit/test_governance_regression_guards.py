from pathlib import Path

ROOT=Path.cwd()

def read(p): return (ROOT/p).read_text(encoding="utf-8")
def test_no_legacy_mcp_probe_tools_restored():
    text="\n".join(p.read_text(encoding="utf-8") for p in (ROOT/"scripts").glob("*mcp*server*.py")) if list((ROOT/"scripts").glob("*mcp*server*.py")) else ""
    for name in ["probe_twse_openapi","probe_tpex_openapi","probe_yahoo_finance","probe_twse_mis","probe_finmind"]: assert name not in text
def test_mcp_governance_docs_remain():
    for p in ["docs/reviews/MCP_01_READONLY_CONTEXT_TOOLS_FIRST.md","docs/reviews/MCP_02_EXPLICIT_CONTROLLED_LIVE_PROBE_TOOLS.md","docs/reviews/MCP_03_GOVERNED_CONTROLLED_EVIDENCE_READBACK.md"]: assert (ROOT/p).is_file()
def test_no_default_script_writes_to_forbidden_paths():
    for p in ["scripts/controlled_refresh_staging_writer.py","scripts/build_frontend_readonly_context_package.py"]:
        text=read(p); assert "is_forbidden_output_dir" in text
def test_staging_writer_requires_confirmations(): assert "REQUIRED_CONFIRMATIONS" in read("scripts/controlled_refresh_staging_writer.py")
def test_frontend_builder_requires_confirmations(): assert "REQUIRED_CONFIRMATIONS" in read("scripts/build_frontend_readonly_context_package.py")
def test_run_all_probes_remains_gated_or_forbidden():
    text=read("scripts/run_all_probes.py").lower(); assert "run_all_probes_i_understand_this_is_live" in text or "forbidden" in text or "legacy" in text
def test_no_test_uses_network():
    for p in (ROOT/"tests/unit").glob("test_*m3k*.py"): assert "requests." not in p.read_text(encoding="utf-8")
def test_no_new_production_refresh_without_confirmations():
    for p in (ROOT/"scripts").glob("*.py"):
        text=p.read_text(encoding="utf-8").lower()
        if "production refresh" in text: assert "confirm" in text
def test_no_buy_sell_hold_or_trading_signal_in_package_schemas():
    for p in ["docs/contracts/frontend_readonly_context_package_schema.md"]:
        text=read(p).lower(); assert "trading_signal`" in text and "false" in text and "buy/sell/hold" in text and "must never present" in text
