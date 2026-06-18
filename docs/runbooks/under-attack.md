# Runbook — Under Attack (DDoS / flood)

**Kiedy odpalany:** alerty *skok połączeń*, *conntrack > 80%*, *ban-rate fail2ban*, *saturacja CPU*, lub *apka nie
zapisuje danych* przy podejrzeniu ataku. Cel: utrzymać MySQL i odzyskać dostępność apki. Zasada: **najpierw potwierdź
warstwę ataku, potem reaguj** — nie strzelaj na oślep.

## 1. Triage — która warstwa? (≤2 min)
- **Logi nginx** (`access.log`) — skok req/s? z jakich IP/ścieżek? typ (GET-flood, slowloris, POST-bomby)?
- Na serwerze: `ss -s` (połączenia), `conntrack -C` vs `nf_conntrack_max`, `mpstat`/`top` (CPU), `fail2ban-client status`.
- **MySQL żyje?** `threads_connected`, `threads_running` — czy to flood połączeń, czy baza już dławi?
- Wniosek: **L3/L4 wolumetryczny** (→ absorbuje sieć Hetznera; my chronimy hosta) vs **L7 aplikacyjny** (→ nginx + host).

## 2. Reakcja
**L7 (najczęstsze) — na hoście, bez CDN:**
- **nginx:** zacieśnij `limit_req` (niższy `rate=`/`burst`) i `limit_conn`, skróć timeouty, w razie potrzeby tymczasowy `return 429` na atakowaną ścieżkę.
- **Blokuj źródła** na poziomie `nftables`/`fail2ban` — IP/podsieci z logów nginx (bany na **realnych IP**, bez CDN są prawdziwe).
- Reguły utrwal w Ansible (rola `nginx`/`fail2ban_config`), nie tylko doraźnie.

**Host / L4:**
- `nftables`: potwierdź synproxy/conn-limit aktywne; dokręć limity połączeń per-IP; podnieś `nf_conntrack_max` jeśli blisko sufitu.
- **Wolumetryka ponad auto-mitygację Hetznera** → zgłoś do Hetzner support (to jedyna realna ścieżka — VM tego nie odbije).
- `fail2ban` — potwierdź bany; w razie potrzeby agresywniejszy jail na 4xx/5xx.

**Ochrona bazy (zawsze sprawdź, że trzyma):**
- Izolacja zasobów: apka nie wyssała RAM/CPU MySQL (`cAdvisor` vs limity; `OOMScoreAdjust` mysqld).
- Per-user limity MySQL (`MAX_USER_CONNECTIONS` itd.) — czy odcinają flood połączeń od apki.
- W ostateczności: skala pionowa serwera (resize) — **bramka płatna, pytaj GO**.

## 3. Weryfikacja odzysku
- Sonda apki (insert→delete) znów **green**; round-trip latency wraca pod SLO.
- `threads_connected`/conntrack/CPU wracają do baseline; ban-rate opada; req/s w nginx spada.

## 4. Po incydencie
- **Postmortem (blameless)** w `../incidents/` — wektor, czas, co zadziałało, co nie, każdy action-item z `Refs #N`.
- Utrwal skuteczne reguły (nginx/`nftables`/`fail2ban`) w Ansible **jako kod**, zdejmij doraźne blokady.
- Dostrój progi alertów, jeśli wykrycie było za wolne. Dopisz wnioski do [security.md](../explanation/security.md).

> Granica (uczciwie): bez CDN duży flood L7 lub wolumetryka ponad auto-mitygację Hetznera **położy publiczną apkę** —
> pojedynczy VM tego nie wygra. Ten runbook **maksymalizuje obronę host/proxy, chroni bazę i skraca powrót**, nie „wygrywa" z floodem łącza.
