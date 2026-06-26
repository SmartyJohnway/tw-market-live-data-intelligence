from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_observability_model_flags():
 t=(ROOT/'frontend/readonly-preview/observabilityModel.js').read_text(); assert 'tradingSignal: false' in t and 'realtimeGuaranteed: false' in t
def test_governance_console_renders_panels():
 t=(ROOT/'frontend/readonly-preview/governance-console.js').read_text();
 for fn in ['renderSourceStatusPanel','renderEvidenceLineagePanel','renderReplayScenarioPanel','renderReleaseReadinessPanel']:
  assert fn in t
 for panel in ['source-status','evidence-lineage','replay-scenarios','release-readiness']:
  assert panel in t
