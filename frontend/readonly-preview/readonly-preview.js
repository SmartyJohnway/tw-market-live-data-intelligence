import {toReadonlyDisplayModel} from './readonlyContextAdapter.js';
import {freshnessBadge, sourceRiskBadge} from './readonlyCaveatBadges.js';
import {sourceAuthorityDisplay} from './sourceAuthorityDisplay.js';
export function renderReadonlyPreview(pkg, root){
  const model=toReadonlyDisplayModel(pkg); root.innerHTML='';
  const banner=document.createElement('p'); banner.textContent='Local preview only: not realtime guaranteed, not a trading signal, not production current state.'; root.appendChild(banner);
  for (const row of model.rows){ const div=document.createElement('div'); div.className='readonly-row';
    div.textContent=`${row.symbol} ${sourceAuthorityDisplay(row.source_id,row.source_authority)} ${freshnessBadge(row.freshness_status)} ${row.delay_status} staleness=${row.staleness_seconds} retrieved=${row.retrieved_at} source=${row.source_timestamp} ${sourceRiskBadge(row.source_risk_flags)} caveats=${row.display_caveats.join(',')}`;
    root.appendChild(div); }
}
