# Phase G V2 contract test snapshot

**NON-AUTHORITATIVE TEST SNAPSHOT.** This directory is a repository-contained
copy of the frozen manifest and examples needed by unit tests to verify the
installed V2 schemas and catalog. It is not a production contract authority,
and runtime code must never load it.

Production authority remains the versioned assets in `schemas/` and
`docs/data_capabilities/unified_market_evidence_capability_catalog.v2.json`.
The snapshot keeps tests portable to clean clones, arbitrary filesystem
locations, Linux runners, and Windows clones without the Owner's external
planning directory.
