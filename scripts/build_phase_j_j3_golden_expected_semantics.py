#!/usr/bin/env python3
"""Rebuild the J3 candidate's J1-derived fields without inventing semantics."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.phase_j_j3_projection import build_content_trace, project_golden
GOLDEN = ROOT / "docs/governance/phase_j/PHASE_J_J3_GOLDEN_EXPECTED_SEMANTICS_V1.json"
TRACE = ROOT / "docs/governance/phase_j/PHASE_J_J3_SEMANTIC_TRACEABILITY_V1.json"
REGISTRY = ROOT / "docs/governance/phase_j/PHASE_J_J0_J1_GOVERNED_SCENARIO_REGISTRY_V1.json"


def main() -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    trace = json.loads(TRACE.read_text(encoding="utf-8"))
    project_golden(registry, golden)
    trace.update(build_content_trace(registry, golden))
    GOLDEN.write_text(json.dumps(golden, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    TRACE.write_text(json.dumps(trace, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
