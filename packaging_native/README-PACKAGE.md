# TW-Market Native Package C

Requires Windows 11 x64 and CPython 3.13 x64. Extract this complete bundle to
a writable application location. The normal operator entry is:

```text
Launch-TW-Market.cmd
```

Double-click it to open the Windows launcher. The launcher detects a suitable
local CPython 3.13 x64 runtime, performs the existing offline bootstrap and
conditional installation init only after an explicit **Set Up TW-Market** action,
and then exposes Start / Stop / Refresh / Diagnose / Open Workbench controls.
It does not install Python, acquire market data, initialize Security Master,
or start the Local Runtime during setup.

The canonical command-line lifecycle remains available for advanced operation:

```powershell
& .\bootstrap\bootstrap.ps1
.\tw-market.cmd status --json
.\tw-market.cmd init
```

Bootstrap verifies the payload, creates `runtime/venv`, and installs only the
included exact hashed wheels with networking disabled for pip. It does not
initialize business state. Status before explicit init is read-only. Use
`--home` / `TW_MARKET_HOME` to select an installation; the default is
`%LOCALAPPDATA%\TW-Market`. Fresh state follows `--state-root`, then
`TW_MARKET_STATE_ROOT`, then HOME/state. Initialized installations retain the
state-root authority in HOME/meta/installation.json.

Use `tw-market.cmd start`, `status`, `doctor`, and `stop`. The MCP stdio entry
is `tw-market-mcp.cmd`; Security Master management is
`tw-market-security-master.cmd`. Security Master acquisition is explicit;
bootstrap, status, and service startup never acquire market data.

The application root is `app`. Keep HOME and STATE_ROOT outside it. The
`runtime` directory is derived, rebuildable, non-canonical runtime, not backup
state. After moving an initialized bundle, remove its entire derived `runtime`
directory and bootstrap at the new location, or extract a fresh copy of the ZIP.
Reuse the same external HOME/STATE to preserve installation identity.

No administrator privileges, registry or PATH changes, system service,
scheduled task, shortcuts, installer, updater, or Docker integration are used.
The distribution manifest detects corruption and accidental payload changes;
its self hash is not an authenticity signature. Signing and a formal SBOM are
future release work. `dependency-manifest.json` records dependency provenance.
