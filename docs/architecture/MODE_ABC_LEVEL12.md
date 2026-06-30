# Mode A/B/C and Level 1/2

## Mode diagram

```mermaid
flowchart LR
  A[Mode A\nCanonical only\nvalidate and inspect M5F] --> B[Mode B\nPlanning + bounded observation\nwatchlist/routes/source health]
  B --> C[Mode C\nAI Conversation Package\nbuild and discuss]
```

## Level diagram

```mermaid
flowchart TB
  L1[Level 1\nvalidated canonical context\nM5F package] --> DISCUSS[Operator / AI discussion]
  L2[Level 2\nbounded observation / temporary context\nM5K latest observation + M5Q source health] --> DISCUSS
  L2 -. never mutates .-> L1
```

Mode A uses Level 1 only. Mode B plans or explicitly creates Level 2 temporary context. Mode C combines Level 1 and Level 2 summaries into the M5N Conversation Package.
