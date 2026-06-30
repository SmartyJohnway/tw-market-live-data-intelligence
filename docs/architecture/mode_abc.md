# Mode A / Mode B / Mode C

## Mode A — Canonical readonly context

Reads the M5F package from disk and exposes it through local surfaces. No network calls and no writes.

## Mode B — Plan live observation

Validates a watchlist and returns adapter routes. This mode is network-free and suitable for frontend and AI planning.

## Mode C — Explicit bounded live observation

Runs a bounded source observation after explicit confirmation. It emits unified observations and failures, records investigation notes, and remains non-canonical.
