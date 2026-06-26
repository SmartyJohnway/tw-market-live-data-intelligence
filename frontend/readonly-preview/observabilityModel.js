export const observabilityModel = {
  sourceStatus: [
    { source_id: "Fixture_Synthetic", risk_flags: ["fixture_only", "validation_only"] }
  ],
  evidenceLineage: ["source fixture", "staging payload", "validator result", "frontend readonly package", "replay summary"],
  replayScenarioSummary: { total_scenarios: 8, failed: 0, productionCurrentStateClaim: false },
  releaseReadiness: { productionReady: false, blockers: ["live probes unauthorized", "production refresh unauthorized"] },
  caveatSeverity: ["info", "warning", "blocked"],
  flags: { tradingSignal: false, realtimeGuaranteed: false, productionCurrentState: false }
};
