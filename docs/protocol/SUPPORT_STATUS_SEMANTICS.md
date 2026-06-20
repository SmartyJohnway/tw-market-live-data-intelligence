# Support Status Semantics

This document defines the strict, stable vocabulary used to describe whether a specific data source supports a given target class. These labels are used in the `SOURCE_TARGET_SUPPORT_MATRIX.md` and related capability reports.

## Status Labels

### `supported_observed`
* **Definition:** Direct evidence exists in the current repository that the source reliably provides data for this target.
* **Evidence Requirement:** Existing probes, offline tests, generated reports, or manually documented sample payloads in the repository.
* **Live Probing Required:** Yes (must have been successfully probed in the past to gain this status).
* **Usable by AI Agents:** Yes (for intended scope, e.g., low-frequency watchlist).
* **Required Caveats:** None inherently, but specific source caveats (like "EOD only" or "unofficial endpoint") still apply.

### `supported_candidate`
* **Definition:** It is highly plausible that the source supports this target based on official documentation or naming conventions, but direct, repeatable evidence is not currently captured in the repository's test/probe suite.
* **Evidence Requirement:** Source documentation, protocol definitions, or external knowledge.
* **Live Probing Required:** Needs to be probed to upgrade to `supported_observed`.
* **Usable by AI Agents:** Proceed with caution; format or availability might differ from expectations.
* **Required Caveats:** Must note that direct repo evidence is lacking.

### `observed_unsupported`
* **Definition:** Direct evidence exists in the current repository that the source explicitly rejects or fails to provide valid data for this target.
* **Evidence Requirement:** Existing probes, offline tests, or generated reports showing failures (e.g., HTTP 404, empty arrays, known placeholder errors).
* **Live Probing Required:** Yes (must have been tested and failed).
* **Usable by AI Agents:** No. Agents must avoid using the source for this target.
* **Required Caveats:** State the specific failure mode (e.g., "Returns HTTP 404 for TX.TW").

### `unsupported`
* **Definition:** The target class is structurally outside the scope or design of the data source.
* **Evidence Requirement:** Basic domain knowledge (e.g., TWSE stock endpoints do not serve TPEx stocks).
* **Live Probing Required:** No.
* **Usable by AI Agents:** No.
* **Required Caveats:** Explain the structural limitation (e.g., "Different exchange venue").

### `auth_required`
* **Definition:** The source likely supports the target, but access requires authentication (API keys, session cookies, broker credentials) that are not currently provided or within the scope of public probes.
* **Evidence Requirement:** Source documentation requiring credentials.
* **Live Probing Required:** Cannot be probed without credentials.
* **Usable by AI Agents:** No, unless the agent environment is explicitly configured with necessary secrets.
* **Required Caveats:** State that credentials are required.

### `doc_only`
* **Definition:** The source is included in the project purely for architectural or documentation purposes. There is no intention to probe it live in the current repository state.
* **Evidence Requirement:** Stated project scope (e.g., Broker APIs without credentials).
* **Live Probing Required:** No.
* **Usable by AI Agents:** No (informational only).
* **Required Caveats:** Explain that it is for design context only.

### `unknown`
* **Definition:** Not enough evidence exists to classify the support level. The target has not been probed, and documentation is unclear or absent.
* **Evidence Requirement:** N/A (lack of evidence).
* **Live Probing Required:** Yes (to resolve the status).
* **Usable by AI Agents:** No.
* **Required Caveats:** State that it is unverified and untested.

### `deferred`
* **Definition:** Determining the support level for this target/source combination is intentionally out of scope for the current milestone.
* **Evidence Requirement:** Milestone constraints.
* **Live Probing Required:** No.
* **Usable by AI Agents:** No.
* **Required Caveats:** Mention which future milestone might address it.
