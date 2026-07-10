# M7G Local Safe Context Artifact Load Policy

Status: `local_safe_context_artifact_load_policy_defined`

M7G allows operator-selected local safe context artifact loading. M7G-00/03 does not execute refresh.

M7G does not allow hidden artifact loading. M7G does not allow auto refresh. M7G does not allow live probe in M7G-00/03. M7G does not allow backend/API/MCP changes in M7G-00/03. M7G does not allow raw payload exposure. M7G does not allow raw forbidden values to render or copy.

M7G does not allow trading advice, recommendation, trading signal, target price, support/resistance, capital flow, sector rotation, full-market breadth, or bullish/bearish claims.

M7G-09 controlled manual refresh execution is mandatory downstream work, because the project must eventually support explicit operator-controlled refresh. M7G-09 must only execute after M7G artifact schema, validator, manual load UI, and refresh request package policy are accepted.

M7G-09 will be the earliest task allowed to execute controlled manual refresh.
