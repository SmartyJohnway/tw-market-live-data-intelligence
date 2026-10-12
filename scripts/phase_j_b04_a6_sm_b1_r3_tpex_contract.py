#!/usr/bin/env python3
"""Offline structural analysis of a supplied TPEx delisting landing capture.

This module emits contract/discovery metadata only. It makes no requests,
resolves no symbolic API expression, and creates no lifecycle events.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit

LANDING_URL = "https://www.tpex.org.tw/zh-tw/mainboard/listed/delisted.html"
CAPTURE_PATH = "data/security_master/input_bundles/m8r06-01b-20261009T180413Z/raw_payloads/tpex_delisted.html"
CAPTURE_SHA256 = "f6eaa4a4969219dc5a633f43e056d8fa2d31fa944c1e23125f24836733f86853"
CAPTURE_SIZE = 11521
CANDIDATE_CLASSES = frozenset({
    "DIRECT_LITERAL_FULL_URL", "DIRECT_LITERAL_ABSOLUTE_PATH",
    "DIRECT_LITERAL_RELATIVE_PATH", "SYMBOLIC_ACTION_TOKEN",
    "EXTERNAL_SCRIPT_DEPENDENCY", "CLIENT_RUNTIME_COMPOSITION_REQUIRED",
    "NOT_A_SOURCE_ENDPOINT",
})
ACQUISITION_DATA_ATTRIBUTES = frozenset({
    "data-autocomplete", "data-start", "data-format", "data-initial",
    "data-url", "data-source", "data-endpoint", "data-api",
})


def sanitized_reference(value: str) -> dict:
    """Expose URL shape without query, fragment, credentials, or raw attribute JSON."""
    parsed = urlsplit(value)
    return {
        "scheme": parsed.scheme.lower() or None,
        "host": parsed.hostname.lower() if parsed.hostname else None,
        "path": parsed.path,
        "query_omitted": bool(parsed.query),
        "fragment_omitted": bool(parsed.fragment),
        "userinfo_omitted": bool(parsed.username or parsed.password),
    }


class LandingInventory(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.doctype_present = False
        self.counts: Counter = Counter()
        self.external_scripts: list[dict] = []
        self.json_script_types: Counter = Counter()
        self.inline_scripts: list[str] = []
        self.data_attributes: list[dict] = []
        self.candidates: list[dict] = []
        self.literal_url_candidates: list[dict] = []
        self._script_attrs: dict | None = None
        self._script_body: list[str] = []

    def handle_decl(self, decl: str) -> None:
        if decl.lower().startswith("doctype html"):
            self.doctype_present = True

    def handle_starttag(self, tag: str, attrs: list) -> None:
        self.counts[tag] += 1
        attributes = dict(attrs)
        if tag == "script":
            self._script_attrs = attributes
            self._script_body = []
            script_type = (attributes.get("type") or "").lower()
            if script_type in {"application/json", "application/ld+json", "application/problem+json"}:
                self.json_script_types[script_type] += 1
            src = attributes.get("src")
            if src:
                ref = sanitized_reference(src)
                self.external_scripts.append({"src": ref, "script_type": script_type or None})
                candidate = {
                    "origin": "script.src", "literal": ref,
                    "classification": "EXTERNAL_SCRIPT_DEPENDENCY",
                }
                self.candidates.append(candidate)
                if ref["scheme"] or ref["host"]:
                    self.literal_url_candidates.append(candidate)
        for attribute in ("href", "action"):
            value = attributes.get(attribute)
            if value:
                ref = sanitized_reference(value)
                candidate = {
                    "origin": f"{tag}.{attribute}", "literal": ref,
                    "classification": "NOT_A_SOURCE_ENDPOINT",
                }
                self.candidates.append(candidate)
                if ref["scheme"] or ref["host"]:
                    self.literal_url_candidates.append(candidate)
        for key in sorted(ACQUISITION_DATA_ATTRIBUTES & attributes.keys()):
            value = attributes[key] or ""
            # Only fixed acquisition/filter attributes; exclude beacon/config tokens.
            self.data_attributes.append({
                "tag": tag, "attribute": key,
                "value": sanitized_reference(value) if key in {"data-url", "data-source", "data-endpoint", "data-api"} else value,
                "classification": "NOT_A_SOURCE_ENDPOINT",
            })

    def handle_data(self, data: str) -> None:
        if self._script_attrs is not None:
            self._script_body.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._script_attrs is not None:
            text = "".join(self._script_body)
            if not self._script_attrs.get("src") and text.strip():
                self.inline_scripts.append(text)
            self._script_attrs = None
            self._script_body = []


def analyze_landing(data: bytes) -> dict:
    parser = LandingInventory()
    parser.feed(data.decode("utf-8-sig", errors="strict"))
    inline = "\n".join(parser.inline_scripts)
    declaration = re.search(r"\b(?:var|let|const)\s+API_PATTERN\s*=|\b(?:window\.)?API_PATTERN\s*=", inline)
    literal = re.search(r"\bAPI_PATTERN\s*=\s*(['\"])([^'\"]*)\1", inline)
    api_reference_count = len(re.findall(r"\bAPI_PATTERN\b", inline))
    action_matches = list(re.finditer(r"\baction\s*:\s*(['\"])([^'\"]*)\1", inline))
    action_candidates = []
    for match in action_matches:
        action_candidates.append({
            "origin": "inline_script.action_property", "literal": match.group(2),
            "classification": "SYMBOLIC_ACTION_TOKEN",
            "syntactic_context": "action property in client initializer",
            "executable_endpoint": False,
        })
    parser.candidates.extend(action_candidates)
    if api_reference_count and not literal:
        parser.candidates.append({
            "origin": "inline_script.pattern_property", "literal": "API_PATTERN",
            "classification": "CLIENT_RUNTIME_COMPOSITION_REQUIRED",
        })
    references = {
        "client_table_initializer_count": len(re.findall(r"\btables\.init\s*\(", inline)),
        "fetch_call_count": len(re.findall(r"\bfetch\s*\(", inline)),
        "xhr_constructor_count": len(re.findall(r"\bXMLHttpRequest\b", inline)),
        "ajax_call_count": len(re.findall(r"(?:\$|jQuery)\.ajax\s*\(", inline)),
        "data_shape_symbolic_references": sorted(set(re.findall(r"\be\.(?:tables|data|fields)\b", inline))),
    }
    return {
        "doctype_present": parser.doctype_present,
        "html_element_present": parser.counts["html"] > 0,
        "table_element_count": parser.counts["table"],
        "form_count": parser.counts["form"],
        "script_element_count": parser.counts["script"],
        "inline_script_count": len(parser.inline_scripts),
        "external_script_src_values": parser.external_scripts,
        "embedded_json_script_blocks": {
            "count": sum(parser.json_script_types.values()),
            "types": dict(sorted(parser.json_script_types.items())),
        },
        "literal_url_candidates": parser.literal_url_candidates,
        "literal_path_action_candidates": parser.candidates,
        "acquisition_data_attributes": parser.data_attributes,
        "client_runtime_references": references,
        "API_PATTERN": {
            "declaration_present": bool(declaration),
            "declaration_absent": not bool(declaration),
            "literal_value_present": bool(literal),
            "literal_value": sanitized_reference(literal.group(2)) if literal else None,
            "symbolic_reference_only": api_reference_count > 0 and not declaration and not literal,
            "reference_count": api_reference_count,
        },
        "company/deListed": {
            "exact_literal_occurrence_count": data.count(b"company/deListed"),
            "syntactic_context": "tables.init action property" if any(c["literal"] == "company/deListed" for c in action_candidates) and references["client_table_initializer_count"] else "unknown",
            "classification": "SYMBOLIC_ACTION_TOKEN" if any(c["literal"] == "company/deListed" for c in action_candidates) else "CLIENT_RUNTIME_COMPOSITION_REQUIRED",
            "executable_endpoint": False,
        },
        "executable_lifecycle_data_endpoint": None,
        "lifecycle_events_generated": 0,
        "lifecycle_dataset_validated": False,
        "source_contract_disposition": "SM_B1_R3_BOUNDED_DISCOVERY_REQUIRED",
    }


def verified_capture(path: Path) -> bytes:
    if not path.is_file():
        raise ValueError("J_B04_A6_SM_B1_R3_BLOCKED_LOCAL_CAPTURE_UNAVAILABLE")
    data = path.read_bytes()
    if len(data) != CAPTURE_SIZE or hashlib.sha256(data).hexdigest() != CAPTURE_SHA256:
        raise ValueError("J_B04_A6_SM_B1_R3_BLOCKED_LOCAL_CAPTURE_HASH_MISMATCH")
    return data


def discovery_proposal(inventory: dict) -> dict:
    targets = []
    reasons = {
        "/rsrc/asset/js/global.js": "Inspect a directly included page configuration dependency for API_PATTERN; its defining asset is not established by the capture.",
        "/rsrc/js/tables.js": "Inspect the directly included client table implementation for pattern/action composition used by tables.init.",
    }
    refs = [item["src"] for item in inventory["external_script_src_values"]]
    for path, reason in reasons.items():
        if not any(ref["path"] == path and ref["scheme"] in (None, "https") and ref["host"] in (None, "www.tpex.org.tw") and not ref["userinfo_omitted"] and not ref["query_omitted"] for ref in refs):
            return {"authorization_readiness": "NOT_READY", "authorization_status": "NOT_AUTHORIZED", "targets": []}
        targets.append({
            "evidence_origin": "preserved landing capture script.src",
            "literal_value": path,
            "candidate_type": "EXTERNAL_SCRIPT_DEPENDENCY",
            "url": urljoin(LANDING_URL, path),
            "official_host": "www.tpex.org.tw",
            "reason_needed": reason,
            "maximum_requests": 1,
            "maximum_followed_redirects": 1,
            "maximum_dispatches": 2,
            "redirect_policy": "HTTPS and same host only; no credentials; no follow-up imports",
            "expected_artifact": "installation-local script capture/hash and sanitized declaration/composition analysis; no raw script published",
        })
    return {
        "authorization_readiness": "EXACT_TARGETS_FROZEN_FOR_OWNER_REVIEW",
        "authorization_status": "NOT_AUTHORIZED",
        "targets": targets,
        "max_logical_requests": 2,
        "max_dispatches_total": 4,
        "retry": 0,
        "timeout_seconds_maximum": 15,
        "response_bytes_maximum_per_target": 1048576,
        "data_endpoint_requests": 0,
        "execute_imported_assets_or_javascript": False,
        "stop_conditions": ["unexpected redirect", "response ceiling breach", "dispatch ceiling breach", "source failure", "missing resolution rule after these two assets"],
        "additional_discovery_requires_new_authorization": True,
        "is_owner_authorization": False,
    }


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--capture", type=Path, required=True)
    args = cli.parse_args()
    inventory = analyze_landing(verified_capture(args.capture))
    print(json.dumps({"structural_inventory": inventory, "future_discovery": discovery_proposal(inventory)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
