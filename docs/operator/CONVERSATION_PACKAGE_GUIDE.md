# Conversation Package Guide

Build:

```bash
python scripts/build_m5n_conversation_context.py
```

Use the package as the AI handoff for Mode C. It combines Level 1 canonical summary with optional Level 2 latest observation/source-health summaries. It is a discussion package, not a data refresh and not a recommendation engine.

When pasting into AI chat, ask for explanation of caveats, source status, freshness semantics, and missing data rather than trading conclusions.
