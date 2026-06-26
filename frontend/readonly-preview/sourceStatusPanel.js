export function renderSourceStatusPanel(sources=[]){return sources.map(s=>`${s.source_id}: ${(s.risk_flags||[]).join(",")}`).join("\n");}
