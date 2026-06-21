# ChatGPT Briefing Policy

## 1. Purpose
This policy dictates the absolute linguistic constraints and behavioral rules for the future ChatGPT Market Briefing generator (M3C-02) and sets the guardrails for AI models reading the generated `chatgpt_briefing.md`. The core tenet is: **observation != signal**.

## 2. Allowed Briefing Language
The briefing must use conservative, descriptive language.
- Allowed to describe the scope boundaries.
- Allowed to describe missing or failed data.
- Allowed to report the recorded observations without judgment.
- Must preserve the distinction between an observation and a signal.

## 3. Prohibited Briefing Language
The briefing and any interpreting AI **must not**:
- Provide buy/sell/hold recommendations.
- Provide rankings (e.g., "Top 5 stocks today").
- Infer or state target prices.
- Provide execution advice.
- Translate observations into trading signals.
- Hide or obfuscate caveats, delays, or failures.

## 4. Source Authority Language Rules
- The wording must clearly distinguish between official End-of-Day (EOD) reference batches, unofficial frontends, third-party APIs, and doc-only capabilities.
- Official realtime data must not be claimed unless explicitly proven by future evidence and authorized by the configuration.

## 5. Freshness and Staleness Language Rules
- The briefing must accurately reflect the staleness, delay, or unknown freshness of the data.
- It must never imply that data is live if it is delayed or EOD.
- "Live candidates" must still be caveated as not officially guaranteed realtime.

## 6. Failure-Envelope Language Rules
If the briefing is generated from a completely failed or offline snapshot:
- It must explicitly declare itself a failure envelope.
- "The latest snapshot contains no successful symbols."
- "Some sources were unavailable, failed, or skipped under offline mode."

## 7. Observation Language Rules
- The term "observation" must be used strictly instead of "signal" or "alert".
- "The available observations are descriptive only and not trading signals."

## 8. Suggested Question Rules
Safe questions steer users towards understanding the system state and the boundaries of the data. They must be purely informational.

## 9. Refusal / Clarification Rules
When the context pack is pasted into an AI, the AI should refuse to answer questions seeking financial advice and instead clarify the boundaries of the context provided. The generated `chatgpt_briefing.md` should instruct the AI to behave this way via the "What AI Must Not Claim" section.

## 10. Examples

**Allowed Language Examples:**
- "This briefing is bounded to the configured watchlist."
- "The current artifact does not establish full-market coverage."
- "The current artifact does not establish official real-time quotes."
- "The latest snapshot contains no successful symbols."
- "The available observations are descriptive only and not trading signals."
- "Some sources were unavailable, failed, or skipped under offline mode."

**Prohibited Language Examples:**
- "The market is live."
- "TWSE officially confirms real-time movement from this context."
- "2330 is a buy."
- "0050 has a target price."
- "This is a strong sell signal."
- "These are the best stocks today."
- "Execute the trade."
- "The whole Taiwan market is covered."

**Safe Suggested Questions:**
- "Which sources failed in the generated context pack?"
- "Which targets failed and why?"
- "What caveats should I keep in mind before interpreting this snapshot?"
- "What can and cannot be safely inferred from this context?"
- "Which source categories are official EOD vs unofficial or third-party?"

**Prohibited Suggested Questions:**
- "Which stock should I buy?"
- "Which target has the strongest signal?"
- "What is the target price?"
- "Should I execute a trade?"
