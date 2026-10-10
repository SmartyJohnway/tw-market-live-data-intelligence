# J-B04-A6-SM-B1-R4 TPEx bounded discovery

Terminal disposition: SM_B1_R4_DISCOVERY_INCONCLUSIVE.

Authorized revision: HEAD feb1df2a86460c5837e8d00f90f48a756b0c0a0d, TREE 3fe87726788bf6b17fd87f5394b077ffbe63feb3; origin/main 6daf6e2dcc6fd34e00e7e3831c25e98bb4d2399a. R3 review ID: 5477064243. Owner statement SHA-256: 3a130da11c04c832823c8e4e1dd2e18e7f7cdb50cae7792eee1e4ef27c7a3709.

Both frozen assets returned HTTP 200, application/javascript, with no redirects and one reserved/observed dispatch each:

| Asset | Bytes | SHA-256 | Result |
|---|---:|---|---|
| global.js | 103202 | 58c3d641bde9aa9c6698ba6145df2a85257ee51f56dc263408a0518e1603e167 | transport success |
| tables.js | 168139 | 085fd65b4e15e2af4f3adb3f256f0058d0176dd2d98ce53217ede16667a04a90 | transport success |

The shared four-dispatch budget used 2. Total GETs 2; HEAD 0; POST 0; retries 0. Both raw files remain only under /tmp/j-b04-a6-sm-b1-r4/raw/. Sanitized transport and analysis receipts and runner hashes are listed in the JSON. No JavaScript ran, no imported asset was fetched, and no inferred data endpoint was called.

Static text inspection found no API_PATTERN declaration in global.js. tables.js contains a generic /{LANG}/{ACTION} default and substitutes the language and action placeholders in opt.pattern; the landing page passes the unresolved API_PATTERN symbol and action token company/deListed. The generic report path uses POST and asks jQuery to parse JSON; form and paging values are supplied at runtime. This does not resolve the landing page pattern, so no candidate endpoint can be stated. The endpoint path and qualified response contract remain unknown.

Security Master remains NOT_INITIALIZED; active selector absent; production identity unverified; bootstrap retry NOT AUTHORIZED. H3/H2/A6 live calls: zero. H2 remains INACTIVE / plan_only with no selected executor; J-B04 BLOCKING; Phase J NOT_STARTED; MCP 6. The R3 pre-probe guard remains in effect.

No production code or manifest was changed. R4 evidence does not promote a production source contract. Independent review is required before any further discovery or endpoint verification.
