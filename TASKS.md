# TASKS — mysql-hetzner-lab (board / roadmapa)

Board docelowo = GitHub Issues + Milestones (Milestone = Faza); ten plik = lustro. „Jak/dlaczego" → `docs/`.
Status: `[ ]` todo · `[~]` doing · `[x]` done.

## Decyzje (ADR)
| # | Decyzja | Wybór | Szczegóły |
|---|---------|-------|-----------|
| 0001 | Provisioning | Terraform + Ansible | [decisions/0001](docs/decisions/0001-provisioning-terraform-ansible.md) |
| 0002 | Backup | XtraBackup + binlog | [decisions/0002](docs/decisions/0002-backup-xtrabackup.md) |
| 0003 | Topologia + offsite | 1 serwer cx22 + Storage Box | [decisions/0003](docs/decisions/0003-topologia-1-serwer.md) |
| 0004 | Repo + CI/CD | GitHub + Actions | [decisions/0004](docs/decisions/0004-github-actions.md) |
| 0005 | Ekspozycja | Aplikacja publiczna + Caddy (bez CDN/VPN) | [decisions/0005](docs/decisions/0005-ekspozycja-publiczna.md) |
| 0006 | Stack monitoringu | Self-hosted Prom+Grafana+Loki on-box | [decisions/0006](docs/decisions/0006-monitoring-stack.md) |

> **Bazujemy na rolach z KontrahentCheck** (bliźniacza infra Hetzner+Ansible) — co kopiować vs budować od nowa: [reuse-from-kontrahentcheck.md](docs/reference/reuse-from-kontrahentcheck.md).

## Cele epica (Definition of Done)
- Reprodukowalność „od zera": `terraform apply` + `ansible-playbook site.yml` odtwarzają cały stack bez ręcznych kroków.
- **RPO ≤ 5 min**, **RTO zmierzony** w drillu (cel < 30 min). **PITR udowodniony** (odzysk sprzed `DROP TABLE`).
- **Aplikacja publiczna, ale utwardzona** (Caddy rate-limit/timeouty + `nftables` + `fail2ban`); **MySQL niepubliczny** (skan: 3306 zamknięty, otwarte tylko 22/80/443).
- CI blokuje PR bez zielonego lint+Molecule+plan; `restore-drill.yml` chodzi na harmonogramie.
- Apka demo w pętli insert→delete po `127.0.0.1`+TLS, user least-priv.

Architektura, diagram, granice → [docs/explanation/architecture.md](docs/explanation/architecture.md).
Obrona/DDoS warstwowo → [docs/explanation/security.md](docs/explanation/security.md).

---

## Fazy

### [~] Faza 0 — Scaffolding & fundamenty `[infra/docs]`
- **Cel:** repo, struktura `docs/`+`ansible/`+`terraform/`+`app/`+`.github/`, ADR-0001..0006, sekrety (**SOPS/age**),
  **pre-commit** (ansible-lint/gitleaks/fmt), `.tool-versions`, Issue/PR templates, lint CI.
- **DoD:** szkielet w repo; ADR-y opisują DLACZEGO; `.gitignore` chroni state/sekrety; lint zielony. **Bramka:** brak.
- **Zrobione:** struktura + configi lint + `ci.yml` (lint) + szablony + `.sops.yaml` (stub); `terraform validate` OK, `ansible-lint` 0 failures.
- **Zostało:** wygenerować klucz **age** i wpiąć do `.sops.yaml` (realne sekrety); ew. `git remote` na GitHub.

### [~] Faza 1 — CI/CD & Test Automation `[infra]` → [ci-cd-and-testing.md](docs/explanation/ci-cd-and-testing.md)
- **Cel:** pipeline egzekwujący jakość + harness Molecule/Testinfra, zanim powstaną role.
- **DoD:** `ci.yml` blokuje PR z błędem lint; harness Molecule gotowy; sekrety zamaskowane.
- **Zrobione:** `ci.yml` (yamllint/gitleaks/terraform), `ansible-test.yml` (ansible-lint+Molecule, bezpieczny gdy brak ról),
  `molecule-template/` + `requirements-dev.txt`, szkielety `deploy`/`restore-drill`/`security-scan` (workflow_dispatch).
- **Zostało:** ożywić `deploy`/drille wraz z Fazami 2/5/6/8; reguła approval `environment: production` w Settings.
- **Bramka:** pierwszy realny `deploy.yml` na żywy serwer — GO.

### [ ] Faza 2 — Infra (Terraform) `[infra]` → [architecture.md](docs/explanation/architecture.md)
- **Cel:** odtwarzalna infra jednym `apply` (cx22, Volume `prevent_destroy`, Storage Box, Hetzner FW).
- **DoD:** `terraform plan` czysty (0 destroy); skan portów = tylko dozwolone; `validate`/`plan` w CI.
- **Bramka:** `terraform apply` / `hcloud create` — pokaż plan, czekaj GO (płatne).

### [~] Faza 3 — Hardening OS (Ansible) `[infra]` → [security.md](docs/explanation/security.md)
- **Cel:** **osobne role** (jak w KontrahentCheck): `common` ✓ · `unattended_upgrades` · `sshd_lockdown` · `fail2ban`
  · `sysctl_hardening` (CIS) · `nftables` (synproxy/conn-limit) · rotacja logów · montaż Volume + Lynis w CI.
- **DoD:** każda rola → Molecule (idempotencja + Testinfra) zielone; `ssh root@` odrzucony; **Lynis score w CI (próg + trend)**.
- **Postęp:** `common` (#2) ✓ · `unattended_upgrades` (#3) ✓ · `sshd_lockdown` (w toku).
- **Bramka:** play mutujący żywy serwer — `--check`, potem GO.

### [ ] Faza 4 — MySQL (Ansible) `[infra]` → [architecture.md](docs/explanation/architecture.md)
- **Cel:** rola `mysql` — bind 127.0.0.1, secure-installation, TLS, least-priv user (per-user MAX_*), binlog ROW, OOM-protect
  **+ ProxySQL** (pooling, miękkie odbicie connection-flood; apka łączy się przez ProxySQL).
- **DoD:** `SHOW MASTER STATUS`=binlogi; `have_ssl=YES`; zdalne `mysql -h <ip>`=timeout; app-user bez `DROP`;
  ruch apki idzie przez ProxySQL. Testinfra asertuje.
- **Bramka:** play mutujący — GO.

### [ ] Faza 5 — Backup (XtraBackup) + restore-drill `[infra]` → [backup-and-recovery.md](docs/explanation/backup-and-recovery.md)
- **Cel:** rola `backup` (nightly XtraBackup → szyfr → Storage Box, retencja) **+ restore-drill w tym samym PR**.
- **DoD:** log backupu + rozmiar offsite; drill odtworzył tabelę (checksum zgodny); RTO zapisany; `restore-drill.yml` zielony.
- **Bramka:** restore tylko na **czystą** maszynę (nie nadpisuj żywej bazy bez GO).

### [ ] Faza 6 — PITR (binlogi) + PITR-drill `[infra]` → [backup-and-recovery.md](docs/explanation/backup-and-recovery.md)
- **Cel:** ciągła archiwizacja binlogów ≤5 min offsite; runbook `pitr.md`.
- **DoD:** PITR-drill odzyskał tabelę sprzed `DROP` (output w runbooku); luka binlogów ≤5 min; PITR w `restore-drill.yml`.
- **Bramka:** drill na czystej maszynie.

### [ ] Faza 7 — Aplikacja demo (Docker) `[app]`
- **Cel:** serwis insert→delete po 127.0.0.1+TLS (przez ProxySQL) **+ sonda SLI** (`/metrics`: sukces cyklu, round-trip latency);
  **+ Caddy reverse-proxy** (publiczny 80/443, auto-TLS LE — rola z KontrahentCheck); hardening kontenera (non-root, read-only, cap_drop, cpus/mem_limit, trivy).
- **DoD:** apka osiągalna publicznie przez HTTPS (Caddy); `docker compose logs` pokazuje cykle; tabela pusta po cyklu; `/metrics` zwraca latency/sukces; `trivy` bez HIGH/CRITICAL; post-deploy smoke OK.
- **Bramka:** lokalny kontener — brak; deploy przez Ansible — GO.

### [ ] Faza 8 — Security / DDoS: utwardzenie publicznej apki + dowód `[infra]` → [security.md](docs/explanation/security.md) · [under-attack.md](docs/runbooks/under-attack.md)
- **Cel:** dostrojenie **Caddy** (rate-limit/timeouty/conn-limit) + `nftables` (synproxy) + jaile `fail2ban`; threat-model STRIDE-lite; **granice (brak CDN) spisane wprost**.
- **+ Drill DDoS (dowód):** kontrolowany load-test (k6/vegeta/hping3) pokazuje, że **MySQL przeżył** (izolacja zasobów) i Caddy/fail2ban złapały flood.
- **DoD:** zewnętrzny skan = 3306 zamknięty, otwarte tylko 22/80/443; drill udokumentowany (wykres przed/po); `security-scan.yml` zielony.
- **Bramka:** zmiany FW/proxy na żywym serwerze — GO.

### [ ] Faza 9 — Observability, alerting & resilience drills `[infra]` → [observability.md](docs/explanation/observability.md)
- **Cel:** **self-hosted Prom+Grafana+Loki+Alertmanager on-box** (ADR-0006) + exportery (node/mysqld/cAdvisor/sonda apki);
  **alerty symptomowe** wg katalogu; **dead-man's-switch ZEWNĘTRZNY** (healthchecks.io); 1 **SLO** (availability+latency)
  z polityką error-budgetu; dashboardy host/MySQL/security/backup. **Przed startem: potwierdź sizing (cx32 lub VictoriaMetrics).**
- **DoD:** każdy critical-alert ma `runbook_url` i przeszedł **test negatywny** (sztucznie wywołany → zadziałał + trafił w kanał);
  monitoring nie wypycha MySQL z RAM (headroom zmierzony); game-day „od zera" odtworzył stack < 1h.
- **Bramka:** stack monitoringu / ew. bump serwera (ADR-0006) — GO.

### [ ] Faza 10 — Portfolio polish `[docs]` (OPCJA)
- **Cel:** **MkDocs (Material) → GitHub Pages** publikujące `docs/`; README z badge'ami (CI, last-restore-drill); diagram jako kod.
- **DoD:** strona zbudowana w CI i opublikowana; linki z README. **Bramka:** brak.

---

## Rozszerzenia — status decyzji
**Wciągnięte do zakresu (wpięte w fazy):**
- Drill DDoS (dowód) → Faza 8 · App jako sonda SLI → Faza 7 · CIS hardening + Lynis → Faza 3 · pre-commit → Faza 0
- ProxySQL → Faza 4 · Secrets rotation + SOPS/age → Faza 0 (+ runbook) · MkDocs → GitHub Pages → Faza 10

**Roadmapa (świadomie później, nie teraz):**
- **CDN/WAF (Cloudflare) jako opcjonalna warstwa** — świadomie odrzucona teraz ([ADR-0005](docs/decisions/0005-ekspozycja-publiczna.md): chronimy publiczny host bez CDN). Gdyby kiedyś — przez Terraform CF provider.
- **Renovate / Taskfile** — dorzucimy przy okazji DX, jeśli się przyda (pre-commit pokrywa minimum).
- **Delayed replica** (replika z opóźnieniem SQL — bufor „oops/ransomware") — wymaga 2. instancji; po ew. bumpie/2. serwerze.

## Świadomie POMIJAMY (roadmapa)
Replikacja/HA (1 serwer = SPOF, pokryte backup/PITR) · Vault/ESM (Ansible Vault+GitHub Secrets) · managed DBaaS
(cel = self-managed) · multi-region/auto-failover/k8s (→ `k8s-hetzner-lab`) · IDS/IPS, własny anycast/scrubbing.

## Następny krok
**Faza 0** (`git init` + `docs/` + ADR-y) → **Faza 1** (CI + harness Molecule). Bezkosztowe. Pierwsza bramka płatna = Faza 2.
