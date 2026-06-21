import json
import os
from datetime import datetime, timezone

def load_json(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Required input file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def validate_context_pack(pack):
    required_sections = [
        "pack_version",
        "generated_at_utc",
        "generated_at_taipei",
        "generation_mode",
        "source_health_summary",
        "source_authority_summary",
        "target_support_summary",
        "latest_snapshot_summary",
        "watchlist_observation_summary",
        "failed_sources",
        "failed_targets",
        "freshness_and_delay_summary",
        "ai_may_say",
        "ai_must_not_claim",
        "mandatory_caveats"
    ]
    for section in required_sections:
        if section not in pack:
            raise ValueError(f"Required top-level section '{section}' is missing from ai_context_pack.json")

def format_bool(value):
    return "true" if str(value).lower() == "true" or value is True else "false"

def format_list(items):
    if not items:
        return ""
    return "\n".join(f"- {item}" for item in items)

def format_dict_counts(mapping):
    if not mapping:
        return "None"
    return ", ".join(f"{k}: {v}" for k, v in mapping.items())

def render_generated_metadata(pack):
    return f"""## Generated Metadata

- **Briefing Generated At (UTC)**: {datetime.now(timezone.utc).isoformat()}
- **Context Pack Version**: {pack.get("pack_version")}
- **Context Pack Generated At (UTC)**: {pack.get("generated_at_utc")}
- **Context Pack Generated At (Taipei)**: {pack.get("generated_at_taipei")}
- **Generation Mode**: {pack.get("generation_mode")}

*Note: The timestamp reflects context pack and briefing generation time, which does not necessarily guarantee live market freshness.*"""

def render_current_scope(pack):
    summary = pack["target_support_summary"]

    text = f"""## Current Scope

This briefing is bounded to the configured watchlist.
Full market coverage: {format_bool(summary.get("full_market_coverage", False))}.

- **Bounded Watchlist Only**: {format_bool(summary.get("bounded_watchlist_only", True))}
- **Target Count**: {summary.get("target_count", 0)}
- **Failed Target Count**: {summary.get("failed_target_count", 0)}
- **Target Classes Observed**: {', '.join(summary.get("target_classes_observed", [])) or 'None'}
- **Target Classes Failed**: {', '.join(summary.get("target_classes_failed", [])) or 'None'}
"""

    if summary.get("target_support_caveats"):
        text += f"\n**Caveats**:\n{format_list(summary.get('target_support_caveats', []))}\n"

    if summary.get("failed_target_count", 0) == summary.get("target_count", 0) and summary.get("target_count", 0) > 0:
         text += "\n**WARNING**: The current context contains no successful market targets.\nNo live market movement summary can be safely produced from this artifact.\n"

    return text

def render_source_health(pack):
    summary = pack["source_health_summary"]
    return f"""## Source Health

- **Total Sources**: {summary.get("total_sources", 0)}
- **Failed/Unavailable Sources**: {summary.get("unavailable_or_failed_sources", 0)}
- **Offline Not Attempted Sources**: {summary.get("offline_not_attempted_sources", 0)}
- **Auth Required Sources**: {summary.get("auth_required_sources", 0)}
- **Doc Only Sources**: {summary.get("doc_only_sources", 0)}

**Source IDs**: {', '.join(summary.get("source_ids", [])) or 'None'}

**Source Health Caveats**:\n{format_list(summary.get("source_health_caveats", []))}"""

def render_source_authority(pack):
    summary = pack["source_authority_summary"]

    live_sources = summary.get("usable_live_sources", [])
    live_sources_text = ', '.join(live_sources) if live_sources else "No usable live source is established by the current context pack."

    return f"""## Source Authority

- **Official Reference (EOD)**: {', '.join(summary.get("official_reference", [])) or 'None'}
- **Unofficial Frontend**: {', '.join(summary.get("unofficial_frontend", [])) or 'None'}
- **Third Party**: {', '.join(summary.get("third_party", [])) or 'None'}
- **Broker Authenticated**: {', '.join(summary.get("broker_authenticated", [])) or 'None'}

- **Usable Live Sources**: {live_sources_text}
- **Usable EOD Sources**: {', '.join(summary.get("usable_eod_sources", [])) or 'None'}
- **Doc Only Sources**: {', '.join(summary.get("doc_only_sources", [])) or 'None'}
- **Auth Required Sources**: {', '.join(summary.get("auth_required_sources", [])) or 'None'}

**Source Authority Caveats**:\n{format_list(summary.get("source_authority_caveats", []))}"""

def render_market_session_status(pack):
    status = pack["latest_snapshot_summary"].get("market_session_status", "unknown")
    return f"""## Market Session Status

- **Status**: {status}

*(Note: If status is unknown, market open/closed status should not be inferred.)*"""

def render_latest_snapshot_summary(pack):
    summary = pack["latest_snapshot_summary"]

    degraded = summary.get("failed_symbol_count", 0) > 0 or summary.get("failed_source_count", 0) > 0
    degraded_text = "\n**Note**: This snapshot is degraded or failed." if degraded else ""

    return f"""## Latest Snapshot Summary

- **Target Count**: {summary.get("target_count", 0)}
- **Symbol Count**: {summary.get("symbol_count", 0)}
- **Failed Symbol Count**: {summary.get("failed_symbol_count", 0)}
- **Failed Source Count**: {summary.get("failed_source_count", 0)}
{degraded_text}

**Global Caveats**:\n{format_list(summary.get("global_caveats", []))}"""

def render_watchlist_observation_summary(pack):
    summary = pack["watchlist_observation_summary"]

    text = f"""## Watchlist Observation Summary

**Important: Observations are descriptive only and not trading signals.**

- **Observations Count**: {summary.get("observations_count", 0)}
- **Failed Observations Count**: {summary.get("failed_observations_count", 0)}

**Observation Type Counts**:
{format_dict_counts(summary.get("observation_type_counts", {}))}

**Severity Counts**:
{format_dict_counts(summary.get("severity_counts", {}))}

**Categories Present**: {', '.join(summary.get("categories_present", [])) or 'None'}
"""
    if summary.get("observations_count", 0) == 0 and summary.get("failed_observations_count", 0) > 0:
        text += "\n**WARNING**: The current observation layer contains failed observations only.\n"

    text += f"\n**Global Caveats**:\n{format_list(summary.get('global_caveats', []))}"
    return text

def render_failed_sources(pack):
    sources = pack.get("failed_sources", [])
    if not sources:
        return "## Failed Sources\n\nNo failed sources are reported in the current context pack."

    table = "## Failed Sources\n\n| source_id | source_type | authority_level | error_type | affected_symbol_count | caveats |\n|---|---|---|---|---|---|\n"
    for s in sources:
        cavs = ", ".join(s.get("caveats", []))
        table += f"| {s.get('source_id', '')} | {s.get('source_type', '')} | {s.get('authority_level', '')} | {s.get('error_type', '')} | {s.get('affected_symbol_count', 0)} | {cavs} |\n"
    return table

def render_failed_targets(pack):
    targets = pack.get("failed_targets", [])
    if not targets:
        return "## Failed Targets\n\nNo failed targets are reported in the current context pack."

    table = "## Failed Targets\n\n| symbol | target_class | failure_reason | source_attempts | caveats |\n|---|---|---|---|---|\n"
    for t in targets:
        atts = ", ".join(t.get("source_attempts", []))
        cavs = ", ".join(t.get("caveats", []))
        table += f"| {t.get('symbol', '')} | {t.get('target_class', '')} | {t.get('failure_reason', '')} | {atts} | {cavs} |\n"
    return table

def render_freshness_delay_staleness(pack):
    summary = pack["freshness_and_delay_summary"]
    return f"""## Freshness / Delay / Staleness

- **Stale Count**: {summary.get("stale_count", 0)}
- **Unknown Freshness Count**: {summary.get("unknown_freshness_count", 0)}
- **EOD Reference Count**: {summary.get("eod_reference_count", 0)}
- **Live Candidate Count**: {summary.get("live_candidate_count", 0)}

**Freshness Status Counts**:
{format_dict_counts(summary.get("freshness_status_counts", {}))}

**Delay Status Counts**:
{format_dict_counts(summary.get("delay_status_counts", {}))}

**Important Rules**:
- Unknown freshness limits interpretation.
- EOD reference does not imply live intraday data.
- Live candidates are not official realtime unless future evidence explicitly proves it.

**Summary Caveats**:\n{format_list(summary.get("summary_caveats", []))}"""

def render_ai_may_say(pack):
    return f"## What AI May Say\n\n{format_list(pack.get('ai_may_say', []))}"

def render_ai_must_not_claim(pack):
    return f"## What AI Must Not Claim\n\n{format_list(pack.get('ai_must_not_claim', []))}"

def render_mandatory_caveats(pack):
    return f"## Mandatory Caveats\n\n{format_list(pack.get('mandatory_caveats', []))}"

def render_suggested_safe_questions():
    questions = [
        "Which sources failed in the generated context pack?",
        "Which targets failed and why?",
        "What caveats should I keep in mind before interpreting this snapshot?",
        "What can and cannot be safely inferred from this context?",
        "Which source categories are official EOD vs unofficial or third-party?",
        "Why is this not a trading signal?",
        "What does bounded watchlist scope mean here?"
    ]
    return f"## Suggested Safe Questions\n\n{format_list(questions)}"

def render_chatgpt_briefing(pack):
    sections = [
        "# ChatGPT Market Briefing",
        render_generated_metadata(pack),
        render_current_scope(pack),
        render_source_health(pack),
        render_source_authority(pack),
        render_market_session_status(pack),
        render_latest_snapshot_summary(pack),
        render_watchlist_observation_summary(pack),
        render_failed_sources(pack),
        render_failed_targets(pack),
        render_freshness_delay_staleness(pack),
        render_ai_may_say(pack),
        render_ai_must_not_claim(pack),
        render_mandatory_caveats(pack),
        render_suggested_safe_questions()
    ]
    return "\n\n".join(sections) + "\n"

def write_text(text, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

def main():
    try:
        input_path = "research/generated/ai_context_pack.json"
        output_path = "research/generated/chatgpt_briefing.md"

        pack = load_json(input_path)
        validate_context_pack(pack)

        briefing_text = render_chatgpt_briefing(pack)
        write_text(briefing_text, output_path)
        print(f"Successfully generated {output_path}")
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1)
    except Exception as exc:
        print(f"UNEXPECTED ERROR: {exc}")
        raise SystemExit(1)

if __name__ == "__main__":
    main()
