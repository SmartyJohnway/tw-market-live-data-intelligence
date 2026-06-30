# Mode A/B/C Walkthrough

## Mode A: validate and inspect canonical context

```bash
python scripts/validate_m5f_canonical_market_context_package.py --package-dir research/staging/m5f/m5f_canonical_market_context_01
python -m json.tool research/staging/m5f/m5f_canonical_market_context_01/canonical_market_context.json | head -80
```

Interpretation: M5F is Level 1, canonical, reviewed, and historical. It is not current observation data.

## Mode B: inspect watchlist/routes/source health and run bounded observation

Plan without network:

```bash
python scripts/run_m5k_postmerge_validation.py --check-only
python scripts/run_m5q_source_health_probe.py --check-only
```

Optional explicit bounded observation:

```bash
python scripts/run_m5k_live_observation.py --watchlist config/m5k_default_watchlist.json --execute-live-observation
```

Interpretation terms: `current observation candidate` means a bounded Level 2 value candidate that still needs caveats; `not_realtime_guaranteed` means do not call it realtime; `not canonical` means it must not overwrite M5F.

## Mode C: build Conversation Package and discuss with AI

```bash
python scripts/build_m5n_conversation_context.py
```

Paste the generated JSON/Markdown into an AI chat and keep the safety text intact: no trading advice, no ranking, no target price, and no buy/sell/hold.
