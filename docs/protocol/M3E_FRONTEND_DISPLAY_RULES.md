# M3E Frontend Display Rules

## Scope and Intent

The M3E Frontend Market Context View is designed to safely expose AI market context artifacts generated during M3 milestones.

**The M3E Frontend is strictly a read-only generated artifact viewer.**

The M3E Frontend is **NOT**:
- a quote board
- a live market dashboard
- a trading dashboard
- a stock screener
- a recommendation engine
- a strategy UI
- a broker interface

## Required Top Banner Language

The frontend must continuously display the following language prominently at the top of the interface:

*   **This context is bounded to the configured watchlist.**
*   **This is not full-market coverage.**
*   **This is not investment advice.**
*   **No official realtime quote guarantee is established.**
*   **Observations are descriptive only and not trading signals.**

## Required View Sections

The frontend must implement the following 10 distinct sections/panels to ensure structured, caveated data presentation:

1.  **Context Status Header**: Displays metadata such as generated time, generation mode, and context pack version.
2.  **Scope Banner**: Displays target counts and clearly defines the bounded watchlist boundaries.
3.  **Source Health & Authority Panel**: Summarizes the 7 canonical sources, explicit authorities (official EOD, unofficial, third-party), and identifies offline or failed sources.
4.  **Latest Snapshot Summary Panel**: Summarizes successful vs. failed symbols across the target scope.
5.  **Watchlist Observation Summary Panel**: Summarizes descriptive observations, grouped by type/severity.
6.  **Failed Sources Table**: Lists explicitly failed infrastructure points.
7.  **Failed Targets Table**: Lists explicitly failed symbols.
8.  **Freshness / Delay / Staleness Panel**: Exposes data quality metrics regarding the timeliness of the snapshot.
9.  **AI Briefing Preview**: A safe, raw-markdown display of the generated ChatGPT briefing.
10. **AI Safety / Must-Not-Claim Panel**: Exposes the centralized governance policies restricting AI interpretations.

## Terminology and Label Rules

To prevent misleading the user, the frontend must strictly adhere to specific nomenclature:

*   Use **"Observations"**, not "Signals".
*   Use **"Targets"**, not "Picks".
*   Use **"Failed Targets"**, not "Bad Stocks".
*   Use **"Source Health"**, not "Realtime Feed Health".
*   Use **"AI Briefing"**, not "Advice".
*   Use **"Context"**, not "Recommendation".

## Prohibited Frontend Wording

The frontend UI itself (labels, buttons, section headers) must **never** use the following terms. These terms are explicitly banned from the application interface, except when they are being explicitly quoted inside the `Prohibited Claims / What AI Must Not Claim` panel.

*   buy
*   sell
*   hold
*   strong signal
*   weak signal
*   target price
*   top picks
*   best stocks
*   ranking
*   momentum score
*   entry point
*   exit point
*   execute trade
*   recommended action