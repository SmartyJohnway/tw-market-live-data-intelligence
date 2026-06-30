# Data Flow

```mermaid
flowchart TB
  TWSE_OPENAPI[TWSE OpenAPI] --> CANON[Canonical / Observation / Source Health]
  TWSE_MIS[TWSE MIS] --> CANON
  TAIFEX_MIS[TAIFEX MIS] --> CANON
  CANON --> CONV[Conversation Package]
  CONV --> API[FastAPI]
  CONV --> FE[Frontend]
  CONV --> MCP[MCP]
  CONV --> AI[AI]
```

TWSE OpenAPI is official reference-style evidence. TWSE MIS and TAIFEX MIS are browser endpoint observation candidates. Every path must keep source time, retrieval time, delay/freshness assessment, caveats, and raw payload policy visible.
