# CI/CD & Testy — mysql-hetzner-lab

Decyzja: [ADR-0004](../decisions/0004-github-actions.md). Dyscyplina (z `CLAUDE.md`): każda rola dostaje testy w swoim PR.

## Piramida testów Ansible
1. **Statyczne:** `yamllint`, `ansible-lint`; Terraform `fmt`/`validate`/`tflint`/`tfsec`; `gitleaks`.
2. **Składnia:** `ansible-playbook --syntax-check`.
3. **Molecule** (sterownik docker/podman) per rola: `converge` + **gate idempotencji** (drugi run = 0 `changed`).
4. **Weryfikacja:** **Testinfra** (pytest) lub `goss` — serwis up, port słucha/zamknięty, config poprawny, user istnieje.
5. **Post-deploy smoke:** po deployu na serwer — MySQL up, binlog ON, apka robi insert→delete, porty zamknięte z zewnątrz.

## Workflowy (`.github/workflows/`)
- **`ci.yml`** (on PR): lint + Molecule + `terraform plan`. **Bez sekretów na PR z forków.** Blokuje merge, gdy czerwone.
- **`deploy.yml`** (on merge to `main` / `workflow_dispatch`): SSH do publicznego hosta (klucz z GitHub Secrets) →
  `ansible-playbook site.yml` → **post-deploy smoke**. `environment: production` z regułą approval.
- **`restore-drill.yml`** (`schedule`, tygodniowo): efemeryczny VM → restore + PITR z offsite → asercje → teardown.
  Egzekwuje „backup bez restore = brak backupu".
- **`security-scan.yml`** (`schedule`): `trivy` obrazu apki + skan portów z zewnątrz (asercja: **3306 zamknięty; otwarte tylko 22/80/443**).

## Runnery
- **GitHub-hosted** do CI (czyste, efemeryczne, bez dostępu do prod).
- **Deploy** po **SSH (key-only)** do publicznego hosta; klucz w GitHub Secrets, `fail2ban` chroni 22. Opcja domknięcia 22 na później:
  self-hosted runner (rola z KontrahentCheck — [reuse](../reference/reuse-from-kontrahentcheck.md)).
- Deploy **nigdy z forka**; akcje mutujące serwer za regułą approval (`environment`).

## Sekrety
GitHub Secrets (zamaskowane): `HCLOUD_TOKEN`, `ANSIBLE_VAULT_PASS`, `TS_OAUTH`, klucze backupu. Zero sekretów w repo —
`gitleaks` pilnuje. Vault-pass podawany do `ansible-playbook` z secreta, nie z pliku w repo.
