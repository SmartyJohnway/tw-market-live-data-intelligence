# Security policy

## Reporting a vulnerability

Please do not publish a proof of concept containing credentials, tokens,
cookies, private market data, or exploit details in a public issue. Contact the
repository owner privately through the security contact shown on the GitHub
repository profile, with a concise reproduction, affected revision, impact,
and safe remediation suggestion.

We will acknowledge a report, assess the affected local-first contract, and
coordinate disclosure before publishing a fix. Do not attempt to bypass
authentication, scrape aggressively, or probe external market systems while
investigating.

## Scope reminders

This project must not accept committed secrets. Security reports involving
MCP, the loopback Local Service, authorization boundaries, package integrity,
or release tooling are in scope. Trading, order routing, and remote account
operations are not product capabilities.
