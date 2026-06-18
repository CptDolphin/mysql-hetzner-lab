# app/ — aplikacja demo (Faza 7)

Serwis FastAPI: pętla **heartbeat** co `HEARTBEAT_INTERVAL` s wykonuje `INSERT → SELECT → DELETE`
(zapisuje rekord do bazy i go kasuje) — żywy smoke-test bazy i **sonda SLI**.

## Endpointy
- `GET /` — status (czy ostatni heartbeat OK).
- `GET /healthz` — 200 gdy baza osiągalna, 503 gdy nie.
- `GET /metrics` — Prometheus: `app_heartbeat_total{result}` + `app_db_roundtrip_seconds`.

## Uruchomienie (dev/CI)
```bash
cd app && docker compose up --build      # apka + własny MySQL
curl localhost:8000/ ; curl localhost:8000/metrics
```

## Konfiguracja (env)
`DB_HOST` `DB_PORT` `DB_USER` `DB_PASSWORD` `DB_NAME` `DB_SSL_CA` `HEARTBEAT_INTERVAL`.
Na prod: `DB_HOST=127.0.0.1`, `DB_PORT=6033` (ProxySQL), TLS przez `DB_SSL_CA`, hasło z sekretu.

## Prod vs dev
- Compose tutaj = **dev/CI** (własny MySQL). Na serwerze apka łączy się do hosta przez ProxySQL,
  kontener hartowany (`read_only`, `cap_drop: ALL`, `no-new-privileges`, limity cpu/mem) i wystawiony przez Caddy.
- App-user na prod jest **least-priv** (bez `CREATE`) — tabelę `heartbeat` tworzy się raz uprzywilejowanym userem.

Szczegóły: [../docs/explanation/architecture.md](../docs/explanation/architecture.md).
