# Product Architecture

```mermaid
flowchart TB
  subgraph L1[Level 1 Canonical]
    M5F[M5F Canonical Package]
  end
  subgraph L2[Level 2 Temporary]
    OBS[M5K/M5L Observation Layer]
    HEALTH[M5Q Source Health]
  end
  M5F --> API[FastAPI]
  M5F --> FE[Frontend readonly workbench]
  M5F --> MCP[MCP]
  OBS --> CONV[M5N Conversation Package]
  HEALTH --> CONV
  M5F --> CONV
  CONV --> AI[AI Discussion]
```

The product separates reviewed canonical context from temporary bounded observations. FastAPI, the frontend, and MCP expose local readonly context or explicit bounded tools; none are trading systems.
