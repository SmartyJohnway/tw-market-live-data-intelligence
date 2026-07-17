# M8R-03E R3 AI policy and evidence schema migration

The package schema remains `v1` because the existing schema permits additional properties and this repository has no external versioned consumer release. This is nevertheless a **consumer-visible breaking field migration**: old `prohibitions` becomes evidence-only `evidence_limitations`; `prohibited_inferences` becomes `calculation_limitations`; `conversation_scope` and `allowed_interpretations` move to AgentPolicy. Historical fields in older inventories remain deprecated compatibility records and are not active evidence truth. See the machine-readable map for consumers and removal timing.

## Versioned strategy

V1 remains immutable and validates historical payloads. V2 is the active builder output. V1 policy fields are migrated only through an explicit adapter: conversation scope and allowed interpretations belong to the handoff/AgentPolicy; factual timing, availability, and calculation constraints become `evidence_limitations` or `calculation_limitations`. V1 manifest count names are rejected for V2 by schema-version mismatch.
