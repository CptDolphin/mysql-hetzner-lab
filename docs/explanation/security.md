# Bezpieczeństwo & DDoS — mysql-hetzner-lab

Decyzja przewodnia: [ADR-0005](../decisions/0005-ekspozycja-publiczna.md).

## Teza
Aplikacja jest **publiczna** (to ona jest celem), baza nie. Świadomie **bez CDN i bez VPN** ([ADR-0005](../decisions/0005-ekspozycja-publiczna.md)) —
ćwiczymy obronę pojedynczego, publicznego hosta. **Mówimy wprost o granicach:** wolumetryczny L3/L4 absorbuje sieć
Hetznera (auto), ale **dużego floodu L7 jeden VM bez edge'a NIE odbije** — i nie ma na to magii w Ansible. Gra toczy się
o trzy rzeczy: **utwardzić host/proxy**, **żeby atak na apkę nie położył bazy** (izolacja zasobów), i **szybko wstać**.

## Ekspozycja: aplikacja publiczna, obrona warstwowa
- **Reverse-proxy nginx** przed apką (80/443): TLS przez certbot (Let's Encrypt), **rate-limit**, **timeouty** (anti-slowloris),
  limity ciała/połączeń. Pierwsza linia filtrowania L7 na hoście (bez CDN).
- **SSH publiczny, utwardzony:** key-only, no-root, `fail2ban`, ew. port niestandardowy. Deploy z CI po SSH (klucz z GitHub Secrets).
- **MySQL niepubliczny** — bind `127.0.0.1`, ruch z apki przez ProxySQL.
- **Hetzner Cloud Firewall:** allow 22/80/443, reszta deny. Origin-IP jawny — akceptowane (patrz Granice).

## Izolacja DB ⟂ apka (1 serwer = wspólny blast-radius)
Realne ryzyko nie brzmi „internet zabije bazę", tylko „apka pod atakiem L7 zje CPU/RAM i wywróci MySQL". Twardo izolujemy:
- Docker `cpus` / `mem_limit` + dodatni `oom_score_adj` kontenera; `OOMScoreAdjust=-800` na unit mysqld → pod presją RAM
  kernel ubija apkę, nie bazę.
- MySQL per-user: `MAX_USER_CONNECTIONS`, `MAX_CONNECTIONS_PER_HOUR`, `MAX_QUERIES_PER_HOUR` — przejęta/oszalała apka
  nie zafloodzi bazy.

## Hardening
- **OS (Ansible):** SSH key-only/no-root, `fail2ban` (bany na **realnych IP** + jaile L7 `nginx-limit-req`/`nginx-botsearch`),
  `nftables`, sysctl, `unattended-upgrades`, **rotacja logów** (log-flood = disk-fill DoS).
- **nftables — limity PER-IP (kluczowe):** zamiast globalnego rate-limitu, `meter { ip saddr ct count over 50 }` i
  `meter { ip saddr limit rate over 25/s }` → **jeden atakujący IP jest throttlowany, nie cały port**. Plus drop
  zniekształconych pakietów (NULL/XMAS/SYN-FIN). SYN-cookies (sysctl). *(synproxy = roadmapa — zależny od modułu jądra.)*
- **sysctl anty-DDoS:** `tcp_synack_retries=2` (szybki drain SYN-backlogu), `somaxconn`, `netdev_max_backlog`,
  `nf_conntrack_max`, `tcp_rfc1337`, krótszy `tcp_fin_timeout`.
- **Reverse-proxy (nginx):** `limit_req`/`limit_conn` per-IP, timeouty (read/write/idle), limit rozmiaru żądania —
  dławi flood L7 i slowloris zanim trafi do apki.
- **MySQL:** bind `127.0.0.1`, `mysql_secure_installation`-równoważnik, `validate_password`, `skip-name-resolve`
  (slow-DNS DoS), TLS, brak zdalnego roota, sensowny `max_connections` + timeouty.
- **Kontener:** non-root, `read_only` + tmpfs, `cap_drop: ALL`, `no-new-privileges`, pin digest, skan `trivy`.

## Warstwy obrony (priorytet)
| Warstwa | Zagrożenie | Mechanizm | Status |
|---------|------------|-----------|--------|
| Sieć Hetzner | Wolumetryczny L3/L4 | Wbudowana ochrona DDoS Hetznera (auto) | **core** |
| Ekspozycja web | L7 flood, slowloris | **nginx** rate-limit + timeouty + conn-limit (na hoście) | **core** |
| Ekspozycja admin | Brute-force SSH | key-only + `fail2ban` + (ew. port niestandardowy) | **core** |
| Edge/CDN | Duży flood L7 / wolumetryka ponad auto | **BRAK (świadomie)** — twardy sufit, patrz Granice | **skip** |
| Host | SYN flood, skan | `nftables` (synproxy/conn-limit), sysctl, `fail2ban` (real-IP) | **core** |
| DB ⟂ apka | Apka zjada zasoby → pada MySQL | Docker limits + `oom_score_adj`; `OOMScoreAdjust=-800` mysqld | **core** |
| MySQL | Connection/query flood | bind 127.0.0.1, per-user `MAX_*`, `skip-name-resolve`, timeouty | **core** |
| Kontener | Eskalacja / zły obraz | non-root, `read_only`, `cap_drop: ALL`, pin digest, `trivy` | **core** |
| Dysk | Log/disk-fill DoS | rotacja logów, `binlog_expire`, retencja backupu, alert disk>80% | **nice** |
| Detekcja | „Nie wiem, że atakują" | alert connection-spike/CPU, logi nginx/fail2ban, runbook under-attack | **nice** (Faza 9) |
| Dane | Wipe/ransomware mimo wszystko | PITR + offsite szyfrowane (inny wektor — i tak musi być) | **core** |
| Enterprise — **pomijamy** | — | własny anycast/scrubbing, mTLS mesh, IDS/IPS (Suricata), HA | **skip** |

## DDoS porządnie = pętla (nie lista regułek)
Same prewencyjne reguły to połowa roboty. Pełna obrona to cykl:
1. **Zapobiegaj** — reverse-proxy (rate-limit/timeouty), hardening host, izolacja zasobów (sekcje wyżej).
2. **Wykryj** — alerty na objawy ataku: skok połączeń, conntrack > 80%, ban-rate fail2ban, saturacja CPU
   ([observability.md](observability.md) — katalog alertów, sygnały oznaczone „DDoS").
3. **Reaguj** — procedura [runbooks/under-attack.md](../runbooks/under-attack.md): zacieśnij rate-limit w nginx,
   dokręć `nftables`/`fail2ban`, blokuj złe sieci, w razie wolumetryki zgłoś do Hetznera; weryfikuj, że izolacja bazy trzyma.
4. **Udowodnij** — **drill DDoS** (kontrolowany load-test, np. `k6`/`vegeta` na L7, `hping3` na host w izolacji):
   pokaż na wykresie, że **MySQL przeżył** (izolacja zasobów), a fail2ban/rate-limit zadziałały. *Dowód, nie deklaracja.*
   Reguły nginx/`nftables`/`fail2ban` trzymane w Ansible **jako kod** — obrona odtwarzalna od zera.

## Granice (czego NIE robimy — uczciwie)
- **Brak edge/CDN = twardy sufit.** Duży flood L7 lub wolumetryka ponad auto-mitygację Hetznera **położy publiczną apkę** —
  pojedynczy VM tego nie wygra. Akceptujemy świadomie (ADR-0005); cel = maksimum obrony host/proxy + przeżycie bazy + szybki powrót.
- **Origin-IP jawny** — bez CDN nie da się go ukryć. Koszt rezygnacji z Cloudflare.
- **1 serwer = SPOF.** Utrata danych pokryta przez PITR (inny wektor niż dostępność).
- Bez anycast/scrubbing-center, IDS/IPS, mTLS-mesh, HA — enterprise/roadmapa. **CDN/WAF (Cloudflare) = świadomie odrzucona warstwa**, nie przeoczenie.

## Threat-model STRIDE-lite
**Główny aktor:** atakujący z internetu (publiczny host). Drugorzędni: przejęta aplikacja, błąd operatora. Insider — n/d w labie.

| Kategoria | Wektor | Kontrola (u nas) | Ryzyko akceptowane |
|-----------|--------|------------------|--------------------|
| **S**poofing | podszycie pod usera/SSH | SSH key-only + `AllowUsers deploy`, app-user least-priv, brak haseł | — |
| **T**ampering | zmiana danych/configu | least-priv (bez `DROP`/`ALL`), `auditd` (watch `/etc/*`, sudoers, mysql), binlog (ślad zmian) | — |
| **R**epudiation | brak śladu kto/co | `auditd` audit-trail + logi nginx/mysql/auth | logi lokalne (offsite logów = roadmapa) |
| **I**nfo disclosure | wyciek danych/sekretów | MySQL `127.0.0.1`, TLS, sekrety w Vault/SOPS (zero w repo), `gitleaks`, kontener non-root/read-only | **origin-IP jawny** (świadomie, bez CDN) |
| **D**oS | flood L7/L4, resource exhaustion | nftables **per-IP** (conn-count + rate), nginx `limit_req`/`limit_conn`, `fail2ban` (SSH+L7), sysctl, **izolacja zasobów apka⟂baza**, Hetzner L3/4 | **duży flood L7 / wolumetryka > pojemność hosta = twardy sufit** (patrz Granice) |
| **E**levation | eskalacja uprawnień | sudo NOPASSWD tylko `deploy`, kontener `cap_drop: ALL`/`no-new-privileges`, sysctl (`kptr_restrict`, `dmesg_restrict`), CIS hardening | — |

**Najważniejsza akceptowana granica:** kategoria **D** — bez CDN pojedynczy VM ma sufit; minimalizujemy powierzchnię i blast-radius, ale nie „wygrywamy" z floodem łącza.
