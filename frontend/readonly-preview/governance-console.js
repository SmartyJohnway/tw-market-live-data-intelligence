import { observabilityModel } from "./observabilityModel.js";
import { renderSourceStatusPanel } from "./sourceStatusPanel.js";
import { renderEvidenceLineagePanel } from "./evidenceLineagePanel.js";
import { renderReplayScenarioPanel } from "./replayScenarioPanel.js";
import { renderReleaseReadinessPanel } from "./releaseReadinessPanel.js";

function setPanelText(id, text) {
  const element = document.getElementById(id);
  if (element) {
    element.textContent = text;
  }
}

export function renderGovernanceConsole(model = observabilityModel) {
  setPanelText("source-status", renderSourceStatusPanel(model.sourceStatus || []));
  setPanelText("evidence-lineage", renderEvidenceLineagePanel(model.evidenceLineage || []));
  setPanelText("replay-scenarios", renderReplayScenarioPanel(model.replayScenarioSummary || {}));
  setPanelText("release-readiness", renderReleaseReadinessPanel(model.releaseReadiness || {}));
  return model;
}

if (typeof document !== "undefined") {
  renderGovernanceConsole();
}
