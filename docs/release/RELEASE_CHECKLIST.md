# Release Checklist

- [ ] M5F validator passes.
- [ ] Non-network tests pass.
- [ ] M5IJ check-only passes.
- [ ] M5K postmerge check-only passes.
- [ ] M5Q check-only passes.
- [ ] Conversation Package builds.
- [ ] FastAPI startup safe: no startup network calls.
- [ ] MCP startup safe: `python server/mcp_server.py --startup-check` passes.
- [ ] Frontend readonly workbench documented.
- [ ] No forbidden path writes.
- [ ] No trading output.
- [ ] No raw payload leakage.
- [ ] No production-ready claim; status remains Local Release Candidate / Not Production Ready.

Commands are listed in [Testing Guide](../contributor/TESTING_GUIDE.md).
