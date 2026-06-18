# Runbook — Point-in-Time Recovery (PITR)

Odtworzenie bazy do **dowolnej sekundy** — np. tuż przed przypadkowym `DROP`/`DELETE`.
**DESTRUKCYJNE** (jak restore) — bramka GO; wykonuj na czystej maszynie.

## Kroki
1. Ustal **target** = czas (UTC) tuż **przed** błędną operacją, np. `2026-06-18 06:25:14`.
2. Restore pełny + replay binlogów do targetu:
   ```bash
   /usr/local/bin/mysql-restore.sh /var/backups/mysql/<TS> "2026-06-18 06:25:14"
   ```
   - `xtrabackup --copy-back` (pełny backup) → start MySQL →
   - `mysqlbinlog --start-position=<z xtrabackup_binlog_info> --stop-datetime="<UTC>" <binlogi> | mysql`
3. Weryfikacja: dane **sprzed** targetu są, **po** — nie.

## RPO / mechanizm
- Binlogi archiwizowane co 5 min (`mysql-binlog-archive.timer`) → **RPO ≤ 5 min**.
- Pozycja startu replayu z `xtrabackup_binlog_info` (zapisana w backupie) — replay nie dubluje danych z backupu.

## Dowód (zautomatyzowany drill)
Molecule roli `restore` (`test_pitr_drill`): insert A → backup → B (czas T1) → C → `DROP` → restore do T1 →
**weryfikacja: A i B odzyskane, C (po T1) nie** — PITR udowodniony w CI, nie deklarowany.
