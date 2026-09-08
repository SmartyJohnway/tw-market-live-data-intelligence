# Portable Skills

`skills/` is the canonical source for portable, reusable Skill packages. It is
not a location for internal Codex prompts, runtime outputs, conversation
artifacts, market-evidence Results, or installation-local Security Master
releases. A packaged ZIP or export is a distribution artifact; an AI handoff
is governed runtime evidence, not a Skill.

| Skill | Role | Primary consumers | Cross-project |
| --- | --- | --- | --- |
| `tw-market-evidence-agent` | Product-facing Portable Skill | External AI and agents using Unified Market Evidence | Limited; product-specific |
| `tw-security-master-classifier` | Reusable Taiwan Market Identity Skill | This repository, other Taiwan-market projects, and AI agents | Yes |

Each package owns its portable instructions, relative references, and offline
validator. Runtime schemas, capability authority, and Security Master releases
remain governed by their repository contracts rather than this index.
