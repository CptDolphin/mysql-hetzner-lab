# Obserwowalność & Alerting — mysql-hetzner-lab

Co śledzimy, na co alertujemy i dlaczego. Stack: [ADR-0006](../decisions/0006-monitoring-stack.md) (pending).
Filozofia: **alert na OBJAW (wpływ na użytkownika/SLO), nie na każdą przyczynę** — przyczyny to warning, objawy to critical.

## SLO (jedno, świadomie)
- **SLI-availability:** % udanych cykli sondy `insert→select→delete` apki demo (to nasz syntetyczny user). **Cel: 99,5% / 30 dni.**
- **SLI-latency:** round-trip do bazy z sondy, **p99 < 50 ms**.
- **Polityka error-budgetu:** budżet OK → wolno ryzykowne zmiany / drille. Budżet spalony → **freeze** niepilnych zmian,
  napraw źródło. SLA = **BRAK** (lab — mówimy wprost).

> Apka demo nie jest tylko „hello world" — jej pętla insert→delete eksportuje metryki sukcesu i latency, więc **jest
> jednocześnie sondą SLI i alarmem „baza żyje"**. To spina cały monitoring.

## Co śledzimy (metryki)
| Źródło | Exporter | Kluczowe sygnały |
|--------|----------|------------------|
| Host | `node_exporter` | CPU/load, RAM (anti-OOM), dysk %, sieć, **conntrack usage**, file descriptors |
| MySQL | `mysqld_exporter` | `threads_connected/running`, `aborted_connects`, slow queries, InnoDB buffer-pool hit, `Questions`, uptime |
| Kontener | `cAdvisor` | CPU/RAM apki vs limity (czy izolacja trzyma) |
| Sonda | apka demo `/metrics` + `blackbox_exporter` | sukces cyklu insert→delete, round-trip latency, endpoint up |
| Bezpieczeństwo | log fail2ban, auth.log, **Caddy access.log** | ban-rate, nieudane logowania, req/s + 4xx/5xx |
| Backup/DR | textfile collector | wiek ostatniego backupu, wynik ostatniego restore-drilla, lag binlogów |

## Logi
MySQL error-log + slow-query-log, `auth.log`, fail2ban, **Caddy access.log**, apka. Pipeline lekki: Promtail/Vector → Loki
(lub journald + zapytania), retencja krótka (lab). Wrażliwe — bez sekretów w logach.

## Katalog alertów
**Critical** (objaw, kanał `#alerts-critical` / Telegram-critical — każdy ma „kto i jak to odczuwa" + `runbook_url`):
| Alert | Sygnał | Próg | Runbook |
|-------|--------|------|---------|
| Apka nie zapisuje danych | sonda insert→delete fail | > 2 min | investigate |
| Baza padła | `mysql_up == 0` | natychmiast | investigate |
| Latency bazy ponad SLO | round-trip p99 | > 50 ms / burn-rate | investigate |
| Dysk pełny | `disk_used` | > 90% | disk-pressure |
| **Backup nie wykonany** (dead-man's-switch) | brak pingu healthchecks.io | > 26 h | restore/backup |
| Cert TLS wygasa | dni do expiry | < 7 dni | cert-rotation |

**Warning** (przyczyna/saturacja, kanał `#alerts-warning`):
| Alert | Sygnał | Próg | Uwaga |
|-------|--------|------|-------|
| Skok połączeń | `threads_connected` / req-rate | > baseline ×3 | **sygnał DDoS** → [under-attack](../runbooks/under-attack.md) |
| Conntrack blisko limitu | `nf_conntrack_count / max` | > 80% | **sygnał DDoS** |
| Ban-rate fail2ban skacze | bany/min | > baseline | **sygnał ataku** |
| Wzrost `aborted_connects` | rate | > baseline | skan/brute / TLS-fail |
| Saturacja CPU/RAM | load / `mem_used` | > 85% 10 min | anti-OOM headroom |
| Lag archiwizacji binlogów | wiek ostatniego binloga offsite | > 5 min | **RPO zagrożone** |
| Slow queries rosną | rate slow-log | > baseline | wydajność |

## Dead-man's-switch (niezależny tor)
Job backupu pinguje **healthchecks.io** po sukcesie; brak pingu → alert **własnym** kanałem healthchecks.io (nie naszym
Alertmanagerem — gdyby padł). Dodatkowo **Watchdog** zawsze-firing potwierdza, że ścieżka Alertmanager→kanał żyje.

## Dashboardy (Grafana)
1. **Host** — CPU/RAM/dysk/sieć/conntrack. 2. **MySQL** — połączenia/QPS/slow/buffer-pool. 3. **Security/DDoS** —
req-rate zza CF, bany, conntrack, skok połączeń. 4. **Backup/DR** — wiek backupu, wynik restore-drilla, gauge RPO.

## Stack — decyzja: self-hosted on-box ([ADR-0006](../decisions/0006-monitoring-stack.md))
**Prometheus + Grafana + Loki + Alertmanager + exportery na serwerze** — cel: nauka pełnego stacku, brak zależności od SaaS.
Świadomie przyjęty trade-off (dzieli failure-domain i RAM z bazą) **wymaga mitygacji OBOWIĄZKOWYCH:**
- **Dead-man's-switch zewnętrzny (healthchecks.io) + zewnętrzny uptime-check** — niezależny tor; alarmuje, gdy serwer
  (a z nim monitoring) pada. Bez tego monitoring ślepnie dokładnie pod atakiem.
- **Budżet RAM** — na 4 GB ciasno: krótka retencja, OOM-priority dla mysqld, **rozważ VictoriaMetrics** (lżejsze niż
  Prom+Loki) **lub bump cx22→cx32 (8 GB)**. Sizing do potwierdzenia. Plan B (jeśli zaboli): hybryda z Grafana Cloud free.

## Świadomie POMIJAMY
Dashboard DORA/MTTR (n małe = szum), tracing/APM, tail-sampling, pełny ELK — enterprise/gold-plating w tym labie.
