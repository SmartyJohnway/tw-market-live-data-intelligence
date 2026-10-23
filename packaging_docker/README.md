# Docker Local Service profile

This profile runs one TW-Market Local Service in a Linux/amd64 container. The
Windows host keeps ownership of the stdio MCP adapter and connects it to
`http://127.0.0.1:<host-port>`. No MCP server, tunnel, agent, database, or other
service runs in the container.

## Build from the exact committed payload

Prepare a clean Linux/amd64 CPython 3.13 wheelhouse using only the checked-in
hashes in `requirements-linux-amd64-cp313.txt`. From a Windows Python 3.13 host:

```powershell
python -m pip download --disable-pip-version-check --no-cache-dir --no-deps `
  --only-binary=:all: --require-hashes --python-version 313 --implementation cp `
  --abi cp313 --platform musllinux_1_2_x86_64 --platform musllinux_1_1_x86_64 `
  --dest C:\twmarket_temp\l6-a4\build\wheelhouse `
  -r packaging_docker\requirements-linux-amd64-cp313.txt
python scripts\build_docker_context.py `
  --wheelhouse C:\twmarket_temp\l6-a4\build\wheelhouse `
  --output C:\twmarket_temp\l6-a4\build\docker-context
docker build --platform linux/amd64 `
  --build-arg SOURCE_TREE=<candidate-tree> `
  --build-arg DEPENDENCY_LOCK_SHA256=<dependency-lock-sha256> `
  --tag tw-market-local-service:l6-a4 `
  --file C:\twmarket_temp\l6-a4\build\docker-context\Dockerfile `
  C:\twmarket_temp\l6-a4\build\docker-context
```

The context builder accepts only exact committed resources from
`packaging_native/resource-policy.json`; it does not copy the repository. Build
installation uses the local wheelhouse with `--no-index`, `--only-binary`, and
`--require-hashes`. Runtime package installation has no network path.

## Explicit initialization and lifecycle

Choose a stable Compose project name for an installation. For acceptance, use a
fresh unique project name. `home` and `state` are named Docker volumes scoped to
that project. Keep the project name to reuse state across container replacement.

```powershell
$env:TW_MARKET_COMPOSE_PROJECT = 'tw-market-local'
$env:TW_MARKET_IMAGE = 'tw-market-local-service:l6-a4'
docker compose -f packaging_docker\compose.yaml run --rm --no-deps `
  --entrypoint python local-service -m scripts.tw_market init --json
docker compose -f packaging_docker\compose.yaml up -d local-service
docker compose -f packaging_docker\compose.yaml ps
docker compose -f packaging_docker\compose.yaml exec -T local-service `
  python -m scripts.tw_market status --json
docker compose -f packaging_docker\compose.yaml exec -T local-service `
  python -m scripts.tw_market doctor --json
docker compose -f packaging_docker\compose.yaml stop local-service
docker compose -f packaging_docker\compose.yaml down
```

`init` is explicit and calls the existing canonical installation initializer.
The service exits when those mounted volumes have not been initialized. Start,
healthcheck, status, and doctor do not initialize state, update the Security
Master, or acquire provider data. `stop` and ordinary `down` preserve volumes.
Do not add `down --volumes` unless intentionally destroying this installation.

## Ownership mapping

| Logical class | Durable root | Docker storage |
|---|---|---|
| Installation metadata and user settings | HOME `meta/`, `config/` | `home` volume |
| Rebuildable cache | HOME `cache/` | `home` volume |
| Logs and operational events | HOME `logs/` | `home` volume |
| Security Master | STATE_ROOT `security-master/` | `state` volume |
| Persistent Watchlists | STATE_ROOT `watchlists/` | `state` volume |
| Governed/control state and retained provenance | STATE_ROOT `governed/` and role-owned subtrees | `state` volume |
| Runtime owner record and temporary work | `/tmp/TW-Market/<installation-id>/` | Ephemeral `/tmp` tmpfs |

The application at `/opt/tw-market/app` and its venv are image content and
read-only during runtime. Named volumes are runtime persistence only; they are
not an L2 backup, export, migration, or restore format.

## Network and host MCP

Compose binds the Windows host side only to
`127.0.0.1:${TW_MARKET_DOCKER_HOST_PORT:-8000}`. The container opts into the
explicit `docker-local-service` network profile. The application still accepts
loopback requests and admits non-loopback requests only from the discovered
private bridge gateway when the server socket remains inside the attached
private subnet. Forwarded headers do not establish authority. Docker publishes
the host side only on loopback; the application does not acquire provider data
during startup or health checks.

Run the existing Windows host MCP adapter with the configured service URL
`http://127.0.0.1:<host-port>`. Its public tool list remains the canonical six.
The Docker profile adds no MCP tool or second API surface.

The image is a local Docker artifact. This package does not publish images,
install a Windows service, or configure auto-start.
