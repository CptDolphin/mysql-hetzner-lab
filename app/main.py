"""Apka demo — żywy smoke-test bazy + sonda SLI.

Pętla heartbeat: INSERT → SELECT → DELETE (zapisuje dane i je kasuje), eksport metryk
Prometheus (sukces cyklu + round-trip latency). Łączy się do MySQL (na prod przez ProxySQL).
"""
import os
import threading
import time
from contextlib import asynccontextmanager

import pymysql
from fastapi import FastAPI, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

DB = dict(
    host=os.getenv("DB_HOST", "127.0.0.1"),
    port=int(os.getenv("DB_PORT", "3306")),
    user=os.getenv("DB_USER", "appuser"),
    password=os.getenv("DB_PASSWORD", ""),
    database=os.getenv("DB_NAME", "appdb"),
    connect_timeout=5,
)
if os.getenv("DB_SSL_CA"):
    DB["ssl"] = {"ca": os.getenv("DB_SSL_CA")}

INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", "10"))

heartbeats = Counter("app_heartbeat_total", "Cykle heartbeat insert->delete", ["result"])
roundtrip = Histogram("app_db_roundtrip_seconds", "Round-trip insert+delete do bazy")
_last = {"ok": False, "ts": None}


def _conn():
    return pymysql.connect(**DB)


def ensure_table():
    # Na prod tabelę tworzy uprzywilejowany user (app-user jest least-priv bez CREATE) —
    # tu best-effort: jeśli brak uprawnień, zakładamy że tabela już istnieje.
    try:
        with _conn() as c, c.cursor() as cur:
            cur.execute(
                "CREATE TABLE IF NOT EXISTS heartbeat "
                "(id BIGINT AUTO_INCREMENT PRIMARY KEY, ts DATETIME NOT NULL)"
            )
            c.commit()
    except pymysql.err.MySQLError:
        pass


def heartbeat_once():
    t0 = time.monotonic()
    with _conn() as c, c.cursor() as cur:
        cur.execute("INSERT INTO heartbeat (ts) VALUES (NOW())")
        rid = cur.lastrowid
        cur.execute("SELECT id FROM heartbeat WHERE id=%s", (rid,))
        cur.fetchone()
        cur.execute("DELETE FROM heartbeat WHERE id=%s", (rid,))
        c.commit()
    roundtrip.observe(time.monotonic() - t0)


def _loop():
    while True:
        try:
            heartbeat_once()
            heartbeats.labels("ok").inc()
            _last.update(ok=True, ts=time.time())
        except Exception:  # noqa: BLE001 — sonda nie może paść, tylko zaznaczyć błąd
            heartbeats.labels("error").inc()
            _last.update(ok=False)
        time.sleep(INTERVAL)


@asynccontextmanager
async def lifespan(_app):
    for _ in range(30):
        ensure_table()
        try:
            with _conn():
                break
        except pymysql.err.MySQLError:
            time.sleep(2)
    threading.Thread(target=_loop, daemon=True).start()
    yield


app = FastAPI(title="mysql-hetzner-lab demo", lifespan=lifespan)


@app.get("/")
def root():
    return {"app": "mysql-hetzner-lab demo", "last_heartbeat_ok": _last["ok"]}


@app.get("/healthz")
def healthz():
    try:
        with _conn() as c, c.cursor() as cur:
            cur.execute("SELECT 1")
        return {"status": "ok"}
    except pymysql.err.MySQLError:
        return Response('{"status":"db-down"}', status_code=503, media_type="application/json")


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
