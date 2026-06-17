# app/ — aplikacja demo (Faza 7)

Mały serwis (FastAPI/Flask lub Node) z pętlą **insert→select→delete** (heartbeat) — żywy smoke-test bazy
i jednocześnie **sonda SLI** (eksport `/metrics`: sukces cyklu + round-trip latency).

- Łączy się po `127.0.0.1` **przez ProxySQL** + TLS, user least-priv (`SELECT/INSERT/DELETE` na jednej tabeli).
- Kontener hartowany: non-root, `read_only` + tmpfs, `cap_drop: ALL`, `no-new-privileges`, limity `cpus`/`mem`.
- Publicznie wystawiona przez **Caddy** (auto-TLS, rate-limit).

Szczegóły: [../docs/explanation/architecture.md](../docs/explanation/architecture.md) · [../TASKS.md](../TASKS.md) (Faza 7).
