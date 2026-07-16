# Current limitations

- Unified Market Evidence Tool API is not implemented in F1.
- MCP, HTTP API, frontend, LLM invocation, polling, notifications, broker integration, and new source adapters are not implemented in F1.
- Existing M8R-03E compatibility fields remain pending migration.
- R2 filesystem containment hardening remains mandatory before Phase C.
- Raw payload exposure remains restricted; normalized evidence is default.
- F1 AI-facing operation names are contract-only and not callable Phase C runtime operations.
- Network-capable underlying producers require M8R-03D controlled execution authorization and are not enabled by default by this Skill.
