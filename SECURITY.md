# Security policy

## Reporting a vulnerability

Please do not publish a proof of concept containing credentials, tokens,
cookies, private market data, or exploit details in a public issue. If GitHub
shows **Report a vulnerability** under this repository's Security tab, use that
private channel with a concise reproduction, affected revision, impact, and
safe remediation suggestion.

If no private channel is available, open a minimal public issue requesting a
private contact path. Do not include exploit details, credentials, tokens,
cookies, private payloads, or proof-of-concept material in that issue.

We will acknowledge a report, assess the affected local-first contract, and
coordinate disclosure before publishing a fix. Do not attempt to bypass
authentication, scrape aggressively, or probe external market systems while
investigating.

## Scope reminders

This project must not accept committed secrets. Security reports involving
MCP, the loopback Local Service, authorization boundaries, package integrity,
or release tooling are in scope. Trading, order routing, and remote account
operations are not product capabilities.
