# Market Evidence Agent Policy

`config/agent_policy/market_evidence_agent_policy.json` is a separately versioned Agent/deployment policy contract. It owns conversational recommendations, advice, signals, response framing, and topic restrictions. Evidence builders and source normalizers must not import it.

The MarketEvidencePackage contains only governed observations, calculations, evidence limitations, missing evidence, lineage, currentness, and citations. A ConversationHandoffEnvelope may apply this policy after evidence construction. Changing policy must not change the package hash, source observations, citations, lineage, currentness, or missing-evidence representation.
