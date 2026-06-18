# Runbook — Restore pełny (XtraBackup)

**DESTRUKCYJNE** — nadpisuje `/var/lib/mysql`. Na żywym hoście = operacja za **bramką GO** (CLAUDE.md).
Domyślnie wykonuj na **czystej** maszynie (restore-drill), nie na produkcji.

## Kroki
1. Wybierz przygotowany backup:
   ```bash
   ls -d /var/backups/mysql/20*
   ```
2. Restore:
   ```bash
   /usr/local/bin/mysql-restore.sh /var/backups/mysql/<TS>
   ```
3. Weryfikacja:
   ```bash
   mysql -e "SHOW DATABASES"
   mysql -e "SELECT COUNT(*) FROM <db>.<tabela>"   # porównaj ze stanem oczekiwanym
   ```

## Mechanizm
`systemctl stop mysql` → opróżnienie datadir → `xtrabackup --copy-back` → `chown mysql:mysql` → `systemctl start mysql`.

## Dowód
Zautomatyzowany w molecule roli `backup` (realny backup) i `restore` (PITR-drill). RTO = zmierzony czas tego skryptu.
