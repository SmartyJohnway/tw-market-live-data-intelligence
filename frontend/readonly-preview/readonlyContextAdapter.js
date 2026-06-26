// Local readonly preview adapter. No realtime guarantee, no trading signal, no production current state.
export function toReadonlyDisplayModel(pkg){
  return {readonlyOnly: pkg.readonly_only === true, globalCaveats: pkg.global_caveats || [], rows: (pkg.symbols || []).map(s => ({
    symbol: s.symbol, source_id: s.source_id, source_authority: s.source_authority, freshness_status: s.freshness_status,
    delay_status: s.delay_status, staleness_seconds: s.staleness_seconds, retrieved_at: s.retrieved_at, source_timestamp: s.source_timestamp,
    data_quality_flags: s.data_quality_flags || [], source_risk_flags: s.source_risk_flags || [], display_caveats: s.display_caveats || [],
    notices: ['not realtime guaranteed','not a trading signal','not production current state']
  }))};
}
