# Recommended Architecture

This document should be filled after experiments.

## Candidate architecture pattern

```text
AI conversation
  ↓
Local market-data tool / MCP server
  ↓
Source adapters
  ├─ official TWSE / TPEx adapter
  ├─ TWSE MIS adapter
  ├─ Yahoo adapter
  ├─ Fugle/Fubon formal API adapter
  └─ fallback screenshot/manual mode
  ↓
Normalized MarketSnapshot schema
  ↓
AI-readable JSON summary
```

## Design requirements

- Source fallback logic
- Timestamp validation
- Staleness detection
- Rate limiting
- Secrets management
- Raw response logging for debugging
- Clear failure messages

## Recommendation status

Pending probe results.
