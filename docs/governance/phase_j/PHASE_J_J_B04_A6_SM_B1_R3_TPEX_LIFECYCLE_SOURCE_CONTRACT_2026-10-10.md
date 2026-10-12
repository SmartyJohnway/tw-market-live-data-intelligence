# J-B04-A6-SM-B1-R3 TPEx lifecycle source contract

Disposition: `SM_B1_R3_BOUNDED_DISCOVERY_REQUIRED`. R2 review: 5476929940.

The exact preserved 11,521-byte capture (SHA-256 `f6eaa4a4969219dc5a633f43e056d8fa2d31fa944c1e23125f24836733f86853`) contains no tables, three forms, fourteen scripts, two inline scripts and no embedded JSON script blocks. `company/deListed` occurs once as a symbolic `tables.init` action; `API_PATTERN` is referenced but neither declared nor assigned a literal value. No executable lifecycle endpoint or valid empty lifecycle dataset is established.

The manifest now distinguishes the verified official client-loaded landing shell from the unresolved lifecycle data contract. Production automatic acquisition is blocked before any probe. The existing TPEx HTML-table parser is unchanged and still rejects shells with `LifecycleSchemaDrift`; supplied legacy tables retain their original lifecycle semantics. Missing evidence never means no lifecycle event.

Future discovery targets are only the directly referenced `https://www.tpex.org.tw/rsrc/asset/js/global.js` and `https://www.tpex.org.tw/rsrc/js/tables.js`. They may help establish configuration and pattern/action composition; neither is asserted to contain the missing rule. Proposed ceiling: two logical requests, one same-host HTTPS redirect and two dispatches per target, four total dispatches, zero retries. No JavaScript execution, crawling, follow-up imports or data endpoint call is proposed. This is metadata, not Owner authorization; no discovery was executed.

SM-B1 and R2 evidence remain byte-identical. Historical manifests explain earlier designs and are not promoted to current authority. TWSE 307 observations remain outside this repair. Security Master remains NOT_INITIALIZED; production identity is not verified. Bootstrap attempt #2 is NOT AUTHORIZED.

Market GET/HEAD/POST: 0/0/0. Security Master acquisition: 0. H2 INACTIVE, route plan_only, selected executor null; J-B04 BLOCKING; Phase J NOT_STARTED; MCP 6. PR #326 remains Draft and unmerged.

The companion JSON contains the sanitized structural inventory, exact source metadata, historical hashes and validation results. No raw capture or script body is published.

Validation: 333 focused tests passed, two skipped; 201 standalone Skill checks passed; all twelve governance validators passed. Compileall and diff checks passed. Strict duplicate-key scan: 1,046 JSON files. Clean-archive default-CI compared the exact baseline against implementation `be90796a935fe786ee31f40084083adbb11d69a7` under identical CPython 3.12.14/dependencies, TZ=UTC, PYTHONHASHSEED=0, and denied sockets. Both retain the same 46 pre-existing failures (including the network-denied localhost vertical); new failure delta is zero. The companion JSON records exact counts and failure IDs. No source calls occurred.
