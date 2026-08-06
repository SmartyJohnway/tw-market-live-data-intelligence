"""Local CLI for M8R-05C: Post-execution AI-context result and audit package projector.

Usage:
    python -m scripts.m8r_05c.cli \\
        --request-input path/to/request.json \\
        --plan-input path/to/plan.json \\
        --authorization-input path/to/authorization.json \\
        --consumption-binding-input path/to/consumption_binding.json \\
        --claim-input path/to/claim.json \\
        --receipt-input path/to/receipt.json \\
        --bundle-input path/to/bundle.json \\
        --artifact-root path/to/artifact_root/ \\
        --out-dir path/to/out_dir/ \\
        [--calculated-at 2026-08-01T10:00:00Z] \\
        [--check-only]

Exit codes:
    0 — success
    1 — projection error (see stderr JSON)
    2 — argument error
    3 — unexpected error

This CLI:
- Makes NO network requests.
- Reads only local files explicitly provided as arguments.
- Writes ONLY to the governed --out-dir.
- Never emits authorization secrets, tokens, credentials, or absolute paths
  on stdout or stderr beyond what the user explicitly provided as arguments.
"""
from __future__ import annotations

import argparse
import json
import sys

from .artifact_loader import load_projection_inputs
from .audit_package_builder import build_audit_package
from .citation_builder import build_citation_index
from .containment import materialize_outputs, validate_output_paths_only
from .errors import ProjectionError
from .lineage_resolver import build_lineage_map
from .markdown_renderer import render_result_markdown
from .result_builder import (
    AUDIT_PACKAGE_RELATIVE_PATH,
    RESULT_RELATIVE_PATH,
    build_result,
)

_RESULT_MD_RELATIVE_PATH = "ai_context/unified_market_evidence_result.v1.md"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="M8R-05C: Project AI-context result and audit package from 05B-03 execution artifacts.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--request-input", required=True, help="Path to the original request JSON.")
    parser.add_argument(
        "--f3-validation-input",
        required=True,
        help="Path to the F3 canonical target validation JSON.",
    )
    parser.add_argument("--plan-input", required=True, help="Path to the orchestration plan JSON.")
    parser.add_argument(
        "--authorization-input", required=True, help="Path to the execution authorization JSON."
    )
    parser.add_argument(
        "--consumption-binding-input", required=True, help="Path to the consumption binding JSON."
    )
    parser.add_argument("--claim-input", required=True, help="Path to the execution claim JSON.")
    parser.add_argument("--receipt-input", required=True, help="Path to the execution receipt JSON.")
    parser.add_argument("--bundle-input", required=True, help="Path to the evidence bundle JSON.")
    parser.add_argument(
        "--artifact-root",
        required=True,
        help="Governed artifact root directory used during 05B-03 execution.",
    )
    parser.add_argument(
        "--out-dir",
        required=True,
        help="Governed output directory for the result and audit package.",
    )
    parser.add_argument(
        "--calculated-at",
        default=None,
        help=(
            "ISO-8601 UTC datetime for generated_at. "
            "If omitted, uses receipt.finalized_at."
        ),
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Validate inputs and output paths without writing any files.",
    )

    args = parser.parse_args(argv)

    try:
        # Load and validate all inputs.
        # Determine calculated_at: use CLI arg if provided, else will use receipt.finalized_at.
        # We defer this decision to after loading the receipt.
        inputs = load_projection_inputs(
            request_path=args.request_input,
            f3_validation_path=args.f3_validation_input,
            plan_path=args.plan_input,
            authorization_path=args.authorization_input,
            consumption_binding_path=args.consumption_binding_input,
            claim_path=args.claim_input,
            receipt_path=args.receipt_input,
            bundle_path=args.bundle_input,
            artifact_root=args.artifact_root,
            # Placeholder — will be resolved below.
            calculated_at="__placeholder__",
        )

        # Resolve calculated_at.
        if args.calculated_at:
            calculated_at = args.calculated_at
        else:
            calculated_at = inputs.receipt.get("finalized_at")
            if not calculated_at:
                raise ProjectionError("calculated_at_missing")
        # Overwrite the placeholder.
        inputs.calculated_at = calculated_at

        if args.check_only:
            # Validate output paths only.
            validate_output_paths_only(
                output_root=args.out_dir,
                result_relative_path=RESULT_RELATIVE_PATH,
                audit_relative_path=AUDIT_PACKAGE_RELATIVE_PATH,
                result_md_relative_path=_RESULT_MD_RELATIVE_PATH,
            )
            print(json.dumps({"status": "check_only_passed"}, sort_keys=True))
            return 0

        # Build result.
        result = build_result(inputs)

        # Build citation index for audit package.
        lineage = build_lineage_map(inputs)
        citation_index = build_citation_index(lineage, inputs.bundle)

        # Build audit package.
        audit_package = build_audit_package(
            result=result,
            inputs=inputs,
            citation_index=citation_index,
            result_relative_path=RESULT_RELATIVE_PATH,
        )

        # Render markdown.
        result_markdown = render_result_markdown(result)

        # Materialize outputs.
        promoted = materialize_outputs(
            output_root=args.out_dir,
            result_json=result,
            audit_package_json=audit_package,
            result_markdown=result_markdown,
            result_relative_path=RESULT_RELATIVE_PATH,
            audit_relative_path=AUDIT_PACKAGE_RELATIVE_PATH,
            result_md_relative_path=_RESULT_MD_RELATIVE_PATH,
        )

        print(
            json.dumps(
                {
                    "status": "success",
                    "result_id": result["result_id"],
                    "result_hash": result["result_hash"],
                    "audit_package_id": audit_package["audit_package_id"],
                    "promoted_files": list(promoted.keys()),
                },
                sort_keys=True,
            )
        )
        return 0

    except ProjectionError as exc:
        print(json.dumps({"error_code": exc.code}, sort_keys=True), file=sys.stderr)
        return 1
    except OSError as exc:
        print(
            json.dumps({"error_code": "io_error", "detail": str(exc)}, sort_keys=True),
            file=sys.stderr,
        )
        return 1
    except Exception as exc:  # noqa: BLE001
        print(
            json.dumps({"error_code": "unexpected_error", "detail": str(exc)}, sort_keys=True),
            file=sys.stderr,
        )
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
