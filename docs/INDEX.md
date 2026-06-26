# Documentation Index

- [Delivery Index](DELIVERY_INDEX.md)
- [Release Readiness](RELEASE_READINESS.md)
- [Glossary](GLOSSARY.md)
- [Source Authority Manual](manuals/SOURCE_AUTHORITY_MANUAL.md)
- [Operator Staging Workflow Manual](manuals/OPERATOR_STAGING_WORKFLOW_MANUAL.md)
- [Frontend Caveat Display Manual](manuals/FRONTEND_CAVEAT_DISPLAY_MANUAL.md)
- [Troubleshooting Guide](manuals/TROUBLESHOOTING_GUIDE.md)
- [Local-First Architecture](architecture/LOCAL_FIRST_MARKET_CONTEXT_ARCHITECTURE.md)

Safe commands: `python -m compileall scripts tests`, `pytest -m "not network"`, and `python scripts/run_local_delivery_acceptance.py --check-only`. Boundaries: no live probes, no production refresh, no frontend/public writes, no trading signals, no realtime guarantee.
