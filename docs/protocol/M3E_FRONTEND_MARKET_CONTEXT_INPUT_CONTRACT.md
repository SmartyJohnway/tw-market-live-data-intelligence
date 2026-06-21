# M3E Frontend Market Context Input Contract

## Overview

The M3E Frontend Market Context View is designed strictly as a read-only viewer for AI market context artifacts. It must respect the boundaries and limitations established by the M3 milestones.

### Core Constraints

1.  **Read-Only:** M3E frontend is read-only.
2.  **No Live Calls:** M3E frontend must not call TWSE, Yahoo, TPEx, FinMind, Fugle, Fubon, or any external endpoint.
3.  **No Probes:** M3E frontend must not run source probes.
4.  **No Mutation:** M3E frontend must not mutate generated artifacts.
5.  **No Inference:** M3E frontend must not infer data that is missing from generated artifacts.
6.  **No Realtime Claims:** M3E frontend must not claim official realtime data.
7.  **No Full Market Claims:** M3E frontend must not claim full-market coverage.
8.  **No Signals:** M3E frontend must not transform observations into signals.

## Permitted Source Artifacts

The frontend is only authorized to read from the following generated JSON and Markdown artifacts located in `research/generated/`:

*   `research/generated/latest_market_snapshot.json`
*   `research/generated/watchlist_observations.json`
*   `research/generated/ai_context_pack.json`
*   `research/generated/ai_context_pack.md`
*   `research/generated/chatgpt_briefing.md`

## Required Frontend Data Groups

The frontend must parse, handle, and display the following data groups mapping directly to paths in the generated artifacts.

### 1. Generated Metadata

| Source Artifact | Source Field Path | Frontend Display Name | Required / Optional | Fallback Behavior | Caveat Visibility | Prohibited Interpretation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `ai_context_pack.json` | `generated_metadata.briefing_generated_at_utc` | Briefing Generated At (UTC) | Required | Display 'Unknown' | Must show note about generation time vs. market freshness | Assuming timestamp guarantees live market freshness |
| `ai_context_pack.json` | `generated_metadata.context_pack_version` | Context Pack Version | Required | Display 'Unknown' | None | Claiming final/production version if draft |
| `ai_context_pack.json` | `generated_metadata.generation_mode` | Generation Mode | Required | Display 'Unknown' | None | Claiming live API fetch if offline |

### 2. Current Scope

| Source Artifact | Source Field Path | Frontend Display Name | Required / Optional | Fallback Behavior | Caveat Visibility | Prohibited Interpretation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `ai_context_pack.json` | `current_scope.bounded_watchlist_only` | Bounded Watchlist Only | Required | Display 'Unknown' | Must display prominently | Claiming full market context |
| `ai_context_pack.json` | `current_scope.full_market_coverage` | Full Market Coverage | Required | Display `true` / 'Unknown' | Critical warning if true or missing | Claiming full market scans or ranking |
| `ai_context_pack.json` | `current_scope.target_count` | Target Count | Required | Display 0 | None | Claiming comprehensive coverage |
| `ai_context_pack.json` | `current_scope.failed_target_count` | Failed Target Count | Required | Display 0 | High visibility if > 0 | Ignoring failed targets |

### 3. Source Health

| Source Artifact | Source Field Path | Frontend Display Name | Required / Optional | Fallback Behavior | Caveat Visibility | Prohibited Interpretation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `ai_context_pack.json` | `source_health.total_sources` | Total Sources | Required | Display 0 | None | N/A |
| `ai_context_pack.json` | `source_health.failed_or_unavailable_sources_count` | Failed/Unavailable Source Count | Required | Display 0 | Must warn if > 0 | Hiding failing infrastructure |
| `ai_context_pack.json` | `source_health.failed_or_unavailable_sources` | Failed/Unavailable Sources | Required | Display `[]` | None | N/A |

### 4. Source Authority

| Source Artifact | Source Field Path | Frontend Display Name | Required / Optional | Fallback Behavior | Caveat Visibility | Prohibited Interpretation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `ai_context_pack.json` | `source_authority.official_reference_eod` | Official Reference (EOD) | Required | Display `[]` | Must note EOD nature | Claiming EOD is live intraday |
| `ai_context_pack.json` | `source_authority.unofficial_frontend` | Unofficial Frontend | Required | Display `[]` | Must note unofficial risk | Claiming unofficial is guaranteed |
| `ai_context_pack.json` | `source_authority.third_party` | Third Party | Required | Display `[]` | Must note third-party status | Claiming official exchange data |

### 5. Market Session Status

| Source Artifact | Source Field Path | Frontend Display Name | Required / Optional | Fallback Behavior | Caveat Visibility | Prohibited Interpretation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `ai_context_pack.json` | `market_session_status.status` | Status | Required | Display 'unknown' | Note if unknown | Inferring market open/closed status |
| `ai_context_pack.json` | `market_session_status.evidence` | Evidence | Optional | Omit | None | N/A |

### 6. Latest Snapshot Summary

| Source Artifact | Source Field Path | Frontend Display Name | Required / Optional | Fallback Behavior | Caveat Visibility | Prohibited Interpretation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `ai_context_pack.json` | `latest_snapshot_summary.symbol_count` | Symbol Count | Required | Display 0 | Note if 0 | N/A |
| `ai_context_pack.json` | `latest_snapshot_summary.failed_symbol_count` | Failed Symbol Count | Required | Display 0 | Warn if > 0 | N/A |
| `ai_context_pack.json` | `latest_snapshot_summary.failed_source_count` | Failed Source Count | Required | Display 0 | Warn if > 0 | N/A |

### 7. Watchlist Observation Summary

| Source Artifact | Source Field Path | Frontend Display Name | Required / Optional | Fallback Behavior | Caveat Visibility | Prohibited Interpretation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `ai_context_pack.json` | `watchlist_observation_summary.observations_count` | Observations Count | Required | Display 0 | None | Treating observations as trading signals |
| `ai_context_pack.json` | `watchlist_observation_summary.failed_observations_count` | Failed Observations Count | Required | Display 0 | Warn if > 0 | N/A |
| `ai_context_pack.json` | `watchlist_observation_summary.observation_type_counts` | Observation Type Counts | Required | Display `{}` | None | N/A |

### 8. Failed Sources

| Source Artifact | Source Field Path | Frontend Display Name | Required / Optional | Fallback Behavior | Caveat Visibility | Prohibited Interpretation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `latest_market_snapshot.json` | `failed_sources` | Failed Sources | Required | Display `[]` | Must note offline/local state | Claiming production live source failure |

### 9. Failed Targets

| Source Artifact | Source Field Path | Frontend Display Name | Required / Optional | Fallback Behavior | Caveat Visibility | Prohibited Interpretation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `latest_market_snapshot.json` | `failed_symbols` | Failed Targets | Required | Display `[]` | None | N/A |

### 10. Freshness / Delay / Staleness

| Source Artifact | Source Field Path | Frontend Display Name | Required / Optional | Fallback Behavior | Caveat Visibility | Prohibited Interpretation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `ai_context_pack.json` | `freshness_delay_staleness.stale_count` | Stale Count | Required | Display 0 | Note stale data | N/A |
| `ai_context_pack.json` | `freshness_delay_staleness.unknown_freshness_count` | Unknown Freshness Count | Required | Display 0 | Note unknown limits | Claiming unknown is fresh |
| `ai_context_pack.json` | `freshness_delay_staleness.live_candidate_count` | Live Candidate Count | Required | Display 0 | Note candidates are not guaranteed | Claiming official realtime |

### 11. AI May Say

| Source Artifact | Source Field Path | Frontend Display Name | Required / Optional | Fallback Behavior | Caveat Visibility | Prohibited Interpretation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `ai_context_pack.json` | `ai_may_say` | What AI May Say | Required | Display `[]` | None | N/A |

### 12. AI Must Not Claim

| Source Artifact | Source Field Path | Frontend Display Name | Required / Optional | Fallback Behavior | Caveat Visibility | Prohibited Interpretation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `ai_context_pack.json` | `ai_must_not_claim` | What AI Must Not Claim | Required | Stop Render (Critical) | High visibility panel | Recommending trades or signals |

### 13. Mandatory Caveats

| Source Artifact | Source Field Path | Frontend Display Name | Required / Optional | Fallback Behavior | Caveat Visibility | Prohibited Interpretation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `ai_context_pack.json` | `mandatory_caveats` | Mandatory Caveats | Required | Stop Render (Critical) | High visibility list | Hiding caveats |

### 14. ChatGPT Briefing Preview

| Source Artifact | Source Field Path | Frontend Display Name | Required / Optional | Fallback Behavior | Caveat Visibility | Prohibited Interpretation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `chatgpt_briefing.md` | Entire File Content | AI Briefing Preview | Required | Display 'Unavailable' | Show `not_investment_advice` | Providing investment advice |