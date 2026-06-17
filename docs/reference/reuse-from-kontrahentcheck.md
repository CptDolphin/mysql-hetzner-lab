# Reuse z KontrahentCheck — co kopiujemy, co budujemy od nowa

Projekt `~/Documents/Claude/Projects/KontrahentCheck` to **bliźniacza infra** (Hetzner + Ansible + hardening + backup/PITR
+ observability + connection-pooler), tyle że na **Postgresie** i w topologii 2-serwerowej.
Reguła: **kopiuj hydraulikę, ZROZUM showcase, zbuduj od nowa warstwę MySQL.** Nigdy `cp -r infra/` — rola po roli.

## Kopiuj wprost (commodity OS — nic nie tracisz, oni to mają dopięte)
`common` · `swap` · `chrony` · `unattended_upgrades` · `logrotate` · `sysctl_hardening` (CIS).

## Kopiuj + ZROZUM (to jest showcase portfolio)
| Rola/asset z KC | Trafia do |
|---|---|
| `hardening`, `sshd_lockdown`, `firewall`, `auditd`, `lynis_audit`, `rkhunter_chkrootkit`, `fail2ban_config` | Faza 3 |
| **`caddy`** (reverse-proxy: auto-TLS LE + rate-limit + timeouty) | Faza 8 — nasza warstwa ekspozycji publicznej |
| `observability_stack`, `promtail_shipper`, `monitoring` + `observability/alertmanager`, `blackbox` | Faza 9 |
| `restic_backup` + workflowy `backup-daily/verify/drill-monthly`, `monthly-dr-drill`, `rollback-drill`, `restore-db.yml`, `disaster-recovery.yml` | Fazy 5/6 (szablon) |
| `.pre-commit-config.yaml`, `.sops.yml`, `.gitleaks.toml`, `.ansible-lint`, `ansible.cfg`, `requirements.yml` | Faza 0/1 |
| `ansible-test.yml`, `drift-check.yml`, `secrets-rotation-reminder.yml`, `create-postmortem.yml`, `oncall-drill.yml` | Faza 1 |

## Buduj OD NOWA (ich jako referencja strukturalna, nie kopia — inna technologia + to rdzeń pokazu)
`postgres_server`/`postgres_setup` → rola **`mysql`** · `pgbouncer` → **`proxysql`** · `wal_g` → archiwizacja **binlogów**;
restic-dump → **XtraBackup**.

## NIE kopiuj
`inventory/`, `group_vars`, `host_vars` (ich topologia 2-serwerowa + sekrety) · role aplikacyjne (`app_deploy`, `aleo_crawler`…) ·
domeny (`weryfikatorpartnera`) · ~50 workflowów `prod-ekrs-*`/`prod-krs-*` (ich apka) · **żadnych sekretów** (`.env`,
`secrets/`, odszyfrowany vault). **SOPS prze-kluczuj na nowo.**

## Świadomie NIE bierzemy (decyzje projektu)
- `cloudflare_*` + `cloudflare_ufw_sync` + CF Access — [ADR-0005](../decisions/0005-ekspozycja-publiczna.md): bez Cloudflare.
- `github_actions_runner` / `runner_*` — tylko jeśli zamkniemy SSH; na razie deploy po SSH key-only.
- `crowdsec` — zostajemy przy `fail2ban` (prościej).

## Metoda (per rola — nie na ślepo)
1. skopiuj katalog roli → 2. przeczytaj `tasks/main.yml` → 3. wytnij specyfikę (AllowUsers, domeny, `/opt/weryfikatorpartnera`,
`T0xx`) → 4. dopisz `molecule/` (u nich „częściowe") → 5. **zielony `ansible-test` = ufasz**. Dopiero wtedy.
