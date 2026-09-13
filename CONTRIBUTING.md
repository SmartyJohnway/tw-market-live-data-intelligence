# Contributing

Thank you for improving this local-first evidence workbench. Start with the
[contributor guide](docs/contributor/CONTRIBUTING.md), [development guide](docs/contributor/DEVELOPMENT_GUIDE.md), and [testing guide](docs/contributor/TESTING_GUIDE.md).

## Before opening a pull request

1. Keep changes small and explain their contract or user-visible effect.
2. Do not add secrets, credentials, cookies, raw personal data, or production
   Security Master / Watchlist state.
3. Preserve explicit authorization, execute-once, and no-trading boundaries.
4. Run the narrowest relevant tests, then the documented validation profile
   when the change affects a public contract or release gate.

Use the bug-report template for reproducible defects and the feature-request
template for proposals. Architecture and governance changes need the relevant
contract and acceptance evidence; they are not implied by an issue alone.

## Development safety

Use isolated local roots for tests. Do not perform external market requests,
Security Master acquisition, or data mutation merely to make a test pass.

## Release status

`1.0.0-rc.1` is a repository candidate only. No RC tag or GitHub prerelease
exists. See [the V1 release candidate guide](docs/release/V1_RELEASE_CANDIDATE.md).
