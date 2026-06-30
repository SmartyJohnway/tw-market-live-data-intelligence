# Source Health Guide

Check-only validation:

```bash
python scripts/run_m5q_source_health_probe.py --check-only
```

Manual bounded execution, only when needed:

```bash
python scripts/run_m5q_source_health_probe.py --execute-health-probe
```

## Status meanings

- `healthy`: representative bounded route worked at retrieval time; still not realtime guaranteed.
- `degraded`: route returned partial, delayed, reference-only, or caveated data.
- `failed`: route failed for the bounded probe; inspect failure reason and recommended next step.
- `unsupported`: product does not support that route/target combination.
- `reference_only`: value is reference semantics, not a current trade observation.
- `stale_or_closed_session`: source appears stale or outside active session.
- `current observation candidate`: bounded Level 2 candidate requiring caveats.
- `not_realtime_guaranteed`: do not describe the value as realtime.
- `not canonical`: do not promote or compare as M5F.
