# ADR-0006 — Stack monitoringu: self-hosted on-box (Prometheus + Grafana + Loki)

- **Status:** zaakceptowany (z zastrzeżeniem sizingu — patrz Konsekwencje)
- **Kontekst:** potrzebna obserwowalność + alerting ([observability.md](../explanation/observability.md)). Cel nauki =
  umieć **samodzielnie postawić i utrzymać** pełny stack. Ograniczenie: 1 serwer cx22 (4 GB), [ADR-0003](0003-topologia-1-serwer.md).

## Decyzja
**Self-hosted Prometheus + Grafana + Loki + Alertmanager + exportery** na tym samym serwerze.

## Konsekwencje
- (+) Pełna kontrola i nauka stacku; brak zależności od SaaS; mocny artefakt portfolio (umiesz to uruchomić).
- (−) **Dzieli failure-domain z bazą** — gdy serwer pada (np. pod DDoS), monitoring ślepnie dokładnie wtedy, gdy go
  potrzebujesz. **Mitigacja OBOWIĄZKOWA:** zewnętrzny **dead-man's-switch (healthchecks.io)** + zewnętrzny uptime-check
  jako niezależny tor alarmowania.
- (−) **RAM** — Prom+Grafana+Loki+MySQL+ProxySQL+app na 4 GB to ciasno; pod presją RAM (a to **cel ataku**) konkurują
  z bazą. **Mitigacja:** krótka retencja, OOM-priority dla mysqld, **rozważ VictoriaMetrics (lżejsze niż Prom+Loki)**
  lub **bump cx22→cx32 (8 GB, ~€11-13/mc)**. Sizing do potwierdzenia przed Fazą 9.

## Alternatywy odrzucone
- **Hybryda (exportery on-box + Grafana Cloud free + healthchecks.io)** — przeżywa awarię serwera i nie zjada RAM bazy;
  odrzucona mimo zalet, bo daje mniej nauki self-hosted i wprowadza zależność od SaaS. (Najbezpieczniejsza operacyjnie —
  trzymamy jako plan B, jeśli RAM/koszt zabolą.)
- **Minimal (cron-checki + healthchecks.io + Telegram)** — za mało sygnału, brak dashboardów i SLO.
