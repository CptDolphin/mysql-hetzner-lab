# Runbook — Under Attack (DDoS / flood)

**Kiedy:** alerty *skok połączeń*, *conntrack > 80%*, *ban-rate fail2ban*, *saturacja CPU*, *apka nie zapisuje danych*.
**Cel:** utrzymać MySQL i odzyskać apkę. **Zasada: najpierw potwierdź warstwę ataku, potem reaguj.**
Komendy jako root. Adresy w `<…>` podmień.

---

## 0. Pierwsze 60 s — szybki obraz
```bash
ss -s                                             # ogólny stan socketów
ss -tn state syn-recv | wc -l                     # half-open (SYN flood?)
cat /proc/sys/net/netfilter/nf_conntrack_{count,max}   # conntrack vs sufit
uptime                                            # load average
# TOP źródłowe IP po liczbie połączeń:
ss -tn | awk 'NR>1{split($4,a,":"); print a[1]}' | sort | uniq -c | sort -rn | head
mysqladmin ping && mysqladmin status              # baza żyje? (jeśli tak — izolacja trzyma)
```

## 1. Triage — która warstwa? (≤2 min)
```bash
# L7 (HTTP): tempo i źródła z logów nginx
tail -n 20000 /var/log/nginx/access.log | awk '{print $1}' | sort | uniq -c | sort -rn | head    # top IP
grep -c 'limiting requests' /var/log/nginx/error.log    # ile trafień rate-limitu (nginx już dławi)
# fail2ban — co już banuje
fail2ban-client status
fail2ban-client status nginx-limit-req
fail2ban-client status sshd
# MySQL — flood połączeń czy baza dławi?
mysql -e "SHOW GLOBAL STATUS WHERE Variable_name IN ('Threads_connected','Threads_running','Aborted_connects')"
mysql -e "SHOW PROCESSLIST" | head -40
```
**Wniosek:**
- Dużo `syn-recv`, conntrack pod sufit, brak konkretnego IP w logach HTTP → **L3/L4 wolumetryczny** (sekcja 2D).
- Jedno/kilka IP dominuje w `access.log`, dużo `limiting requests` → **L7 aplikacyjny** (2A).
- Brute-force SSH w `fail2ban status sshd` → 2B. `Threads_connected` przy `max_connections` → 2C.

---

## 2. Reakcja (scenariusze — copy-paste)

### 2A. Flood HTTP (L7) — najczęstsze
```bash
# (1) Natychmiast i TRWALE zablokuj źródło — set @blackhole (przeżywa `systemctl reload nftables`):
nft add element inet filter blackhole { <IP> timeout 1h }          # pojedynczy IP, auto-wygasa po 1h
nft add element inet filter blackhole { <CIDR>/24 timeout 1h }     # cała podsieć, jeśli rotują IP
nft add element inet filter blackhole6 { <IPv6> timeout 1h }       # odpowiednik dla IPv6
#   Podgląd/zdjęcie bana: nft list set inet filter blackhole  |  nft delete element inet filter blackhole { <IP> }
#   (Doraźne `nft insert rule inet filter input ip saddr <IP> drop` też tnie od razu, ale GINIE po reloadzie reguł — wolimy set.)
# (2) Albo przez fail2ban (spójne z banaction nftables, z czasem bana):
fail2ban-client set nginx-limit-req banip <IP>
# (3) Zaostrz rate-limit globalnie (edytuj, potem reload — nginx NIE gubi połączeń):
sed -i 's/rate=30r\/s/rate=10r\/s/' /etc/nginx/conf.d/00-ratelimit.conf
nginx -t && systemctl reload nginx
# (4) Awaryjnie utnij atakowaną ścieżkę (dopisz w /etc/nginx/conf.d/app.conf w bloku 443):
#     location = /atakowana { return 429; }
nginx -t && systemctl reload nginx
# (5) LOAD-SHEDDING — gdy źródeł jest ZA DUŻO by blokować po IP: serwuj tanią odpowiedź
#     zamiast obciążać apkę/bazę. W bloku 443 podmień `location /` na:
#       location / { limit_req zone=applimit burst=5 nodelay; return 503 "busy\n"; }
#     (zero ruchu do apki/MySQL — backend oddycha). Reload jak wyżej.
# (6) PÓŁ-AUTOMAT — banuj najgłośniejsze IP w pętli (botnet = ręcznie się nie wyrobisz):
watch -n 30 'tail -n 5000 /var/log/nginx/access.log | awk "{print \$1}" | sort | uniq -c \
  | sort -rn | awk "\$1>500{print \$2}" | while read -r ip; do fail2ban-client set nginx-limit-req banip "$ip"; done'
```

### 2B. Brute-force SSH
```bash
fail2ban-client status sshd                 # sprawdź aktywne bany
fail2ban-client set sshd banip <IP>         # ręczny ban
nft insert rule inet filter input tcp dport 22 ip saddr <CIDR>/24 drop   # twarda blokada podsieci
# SSH i tak: key-only + AllowUsers deploy (rola sshd_lockdown) — hasła nie przejdą.
```

### 2C. Wyczerpanie połączeń MySQL
```bash
mysql -e "SHOW PROCESSLIST" | awk '$2=="appuser"' | head       # połączenia app-usera
# per-user limity (rola mysql: MAX_USER_CONNECTIONS) już ograniczają appusera —
# jeśli to one trzymają, baza odrzuca nadmiar, nie pada. Potwierdź:
mysql -e "SHOW GLOBAL STATUS LIKE 'Threads_connected'"
# Awaryjnie ubij konkretne połączenie:
mysql -e "KILL <id>"
# Jeśli to apka oszalała — zrestartuj kontener (baza zostaje):
docker compose -f /opt/mysql-lab-app/docker-compose.prod.yml restart app
```

### 2D. SYN flood / wolumetryczny (L4)
```bash
# SYN-cookies + per-IP metery już działają (role sysctl_hardening, nftables). Potwierdź:
sysctl net.ipv4.tcp_syncookies                    # = 1
nft list ruleset | grep -A2 'meter web-'          # per-IP conn/rate aktywne
# Conntrack pod sufitem → podnieś tymczasowo:
sysctl -w net.netfilter.nf_conntrack_max=524288
# WOLUMETRYKA ponad auto-mitygację Hetznera = jedyna realna ścieżka:
#   Hetzner Cloud Console → Server → włącz/sprawdź DDoS protection / zgłoś ticket.
#   Pojedynczy VM tego nie „odbije" (patrz Granice).
```

### Zawsze sprawdź, że BAZA trzyma (cel nadrzędny)
```bash
mysqladmin ping                                   # MySQL żyje?
mysql -e "SHOW GLOBAL STATUS LIKE 'Threads_running'"
# OOMScoreAdjust=-800 + limity Dockera apki → kernel ubije apkę, nie mysqld.
dmesg -T | grep -i 'killed process' | tail         # czy OOM-killer coś ruszył?
```
W ostateczności skala pionowa (resize cx22→cx32) — **bramka płatna, pytaj GO.**

---

## 2E. Eskalacja — gdy host nie wystarcza (recurring / duży / rozproszony DDoS)
**Uczciwie: pojedynczy VM bez CDN nie wygra z botnetem (tysiące rotujących IP) ani z floodem łącza.** Host-level
(sekcje 2A-2D) zatrzymuje pojedyncze/kilka źródeł, brute-force, connection-flood — rozproszony L7 i wolumetrykę przerośnie.

**Jeśli DDoS jest CZĘSTY → właściwym rozwiązaniem jest edge/CDN przed apką** (świadomie odrzucony w
[ADR-0005](../decisions/0005-ekspozycja-publiczna.md), ale to break-glass i prawdopodobnie sygnał, że trzeba zmienić ADR).

**Break-glass: Cloudflare przed apką (~15 min):**
1. Dodaj domenę do Cloudflare; rekord A z **proxy ON** (pomarańczowa chmurka) — origin-IP znika za edge.
2. **Under Attack Mode** (Security → Settings) — challenge JS/Turnstile dla całego ruchu.
3. WAF **rate-limiting rule** + managed rules; blokada ASN/kraju z analytics, jeśli atak skupiony.
4. **Zamknij origin:** w Hetzner FW wpuść 443 **tylko z zakresów IP Cloudflare** (origin nieosiągalny wprost).

Wtedy wolumetrykę i rozproszony L7 absorbuje Cloudflare; host robi tylko backend. **Gdy DDoS jest regularny, to nie
gold-plating — to brakująca warstwa.** Zostaje na stałe → spisz nowy ADR (zmiana ekspozycji).

---

## 3. Weryfikacja odzysku
```bash
ss -tn state syn-recv | wc -l                      # half-open spada
cat /proc/sys/net/netfilter/nf_conntrack_count     # conntrack wraca do baseline
curl -fsS https://localhost/healthz -k             # apka odpowiada (przez nginx)
mysqladmin ping                                    # baza żyje
tail -n 2000 /var/log/nginx/access.log | wc -l     # req/s opada
```
Sonda apki (insert→delete) znów green, round-trip latency pod SLO.

## 4. Po incydencie
- **Utrwal skuteczne blokady jako kod** (element `@blackhole` przeżywa reload, ale NIE reboot ani re-run roli — `nft insert` ginie już po reloadzie):
  - trwały ban IP/podsieci → rola `fail2ban`/`nftables` (PR), nie tylko `nft add element`/`nft insert`.
  - nowy próg rate-limit → `nginx_rate_limit`/`nginx_rate_burst` w roli `nginx` (PR).
- **Postmortem (blameless)** w `docs/incidents/<data>.md` (folder przy 1. incydencie): wektor, czas wykrycia/reakcji, co zadziałało, action-items z `Refs #N`.
- Dostrój progi alertów, jeśli wykrycie było za wolne. Wnioski → [security.md](../explanation/security.md).

---

> **Granica (uczciwie):** bez CDN duży flood L7 lub wolumetryka ponad auto-mitygację Hetznera **położy publiczną apkę** —
> pojedynczy VM tego nie wygra. Ten runbook **maksymalizuje obronę host/proxy, chroni bazę i skraca powrót**, nie „wygrywa" z floodem łącza.
