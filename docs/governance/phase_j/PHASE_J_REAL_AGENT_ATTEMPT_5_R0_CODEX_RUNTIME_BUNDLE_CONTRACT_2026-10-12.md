# Phase J Attempt #5-R0 — Complete Codex Runtime Bundle Pinning

Disposition: `PHASE_J_REAL_AGENT_ATTEMPT_5_R0_COMPLETE_CODEX_RUNTIME_BUNDLE_READY_FOR_INDEPENDENT_REVIEW`

## Authority and repair

Starting HEAD/TREE: `083d636d7315372dd0c6defb4f2bdc398f1155ed` / `03f312ef67ce44714ddd31cd177016baf629af1a`. Attempt #4 review `5488441715` accepted the terminal finding `PHASE_J_REAL_AGENT_ATTEMPT_4_HARD_BLOCK_CODE_MODE_HOST_UNAVAILABLE`. The executable-only pin lacked the vendor sibling `codex-code-mode-host.exe`; unused Attempt #4 slots are not transferable. The successor model pins the complete vendor runtime bundle.

## Bundle identity

The source vendor directory and the distinct Git-external target
`D:\Codex-Workspace\runtime\tw-market-live-data-intelligence\phase-j-real-agent-r4-r2\codex-pinned\0.160.1-bundle`
each contain 45 files totaling 450,588,539 bytes. Their sorted per-file path/size/SHA-256 manifests match one-for-one. Canonical inventory SHA-256:
`5e0e4b9752aa06cc0d8609168cae658efcd1c544160272f8a64f3a1c1ea08629`.
The full manifests, measured helper identities, and launch contract are recorded in the paired JSON.

The pinned executable is `bin\codex.exe`, observed as `codex-cli 0.160.1`, size 326,875,440 bytes, SHA-256 `9e7c59c05cc1ce5677b1f94e835b2ac038ca3be14504e78d558eacdb0ea3f55d`. Its same-bundle Code Mode host is `bin\codex-code-mode-host.exe`, size 74,669,360 bytes, SHA-256 `b905b5169bd758dbe3c31ca22c22ad0c24df0047ba7ae32652c706d3ac3ba78d`. The command runner and sandbox helper identities are also pinned in the manifest. No executable or helper binary is committed.

## Successor contract and preflight

The `phase_j_real_agent_attempt_5_launch_contract.v1` contract SHA-256 is
`01f51f75dc62f01afef9ed2c260c02439d3ddf73b8447e98d471335c0019aeb3`.
It binds the full bundle, retained R4-R2 package, neutral prompt, existing required `phase_j_witness` proxy, exact six-tool list, two-call semantic policy, and three deterministic evidence slots. `verify_contract_runtime_identity()` remeasures the complete bundle and contract hash for the pre-reservation gate. Attempt #5 reserved/launched slots remain zero.

The bundled CLI reported version `codex-cli 0.160.1`; its `exec --help` supports `--ignore-user-config`. In isolated configuration, `mcp list` and `mcp get phase_j_witness` exited successfully and showed the intended single witness server. The supplied override sets `required=true`; the CLI JSON readback does not project that field. Local Service health was healthy on contract v2 with 14 capabilities. A direct stdio proxy probe passed initialize and tools/list with the exact six tools; its event log is hash-bound in the JSON. Semantic MCP calls were zero. Login status reported ChatGPT authentication; no provider session was launched.

## Boundaries and state

The retained R4-R2 package identities remained unchanged. Provider inference, real-agent sessions, Attempt #5 slots, semantic MCP calls, market GET/HEAD/POST, J1-21 executions, Browser Use, Firecrawl, Security Master acquisition/mutation, production changes, and MCP surface changes were all zero.

`remaining_obligations=["real_agent_layer"]`; Phase J remains STARTED, Roadmap Phase J remains unchecked, Phase K remains NOT_STARTED, and PR #326 remains OPEN / Draft / unmerged. This tranche grants no closure credit and does not start Attempt #5.
