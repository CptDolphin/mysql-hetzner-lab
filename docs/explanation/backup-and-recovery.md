# Backup, Restore & PITR — mysql-hetzner-lab

Decyzja: [ADR-0002](../decisions/0002-backup-xtrabackup.md). Zasada nadrzędna (z `CLAUDE.md`):
**backup bez przetestowanego restore = brak backupu.**

## Cele (RPO / RTO)
- **RPO ≤ 5 min** — binlogi archiwizowane co ≤5 min.
- **RTO** — mierzony w restore-drillu (cel < 30 min dla pełnego restore). Zapisywany jako dowód, nie założenie.

## Pełny backup
**Percona XtraBackup 8.0** (hot, nieblokujący, wspiera inkrementalne), nightly przez systemd-timer →
szyfrowanie (age/gpg) → `restic`/SFTP do **Hetzner Storage Box**. Retencja: 7× dzienny + 4× tygodniowy.

## PITR (point-in-time recovery)
- Wymóg: `log_bin` ON, `binlog_format=ROW`, sensowny `binlog_expire_logs_seconds`.
- **Ciągła archiwizacja binlogów** co ≤5 min (`mysqlbinlog --read-from-remote-server --stop-never` lub flush+ship),
  szyfrowane, offsite.
- Odtworzenie: pełny restore z XtraBackup → `mysqlbinlog` replay binlogów do `--stop-datetime` (sekunda sprzed awarii).

## Drille (obowiązkowe, automat — `restore-drill.yml`)
- **restore-drill:** odtwórz pełny backup na **czystej** maszynie, porównaj checksumy, zmierz RTO.
- **PITR-drill:** wstaw dane → zanotuj czas `T` → `DROP TABLE` → restore + replay do sprzed `T` → udowodnij odzysk.
- Oba na harmonogramie (scheduled), nie raz ręcznie. To one zamieniają „mamy backup" w „mamy odtwarzalność".

## Runbooki
- `../runbooks/restore.md` — pełny restore (powstaje w Fazie 5).
- `../runbooks/pitr.md` — odtworzenie do punktu w czasie (powstaje w Fazie 6).

## Granica
Restore **nigdy** nie nadpisuje żywej bazy bez GO (bramka w `CLAUDE.md`). Drille lecą na osobnej, czystej maszynie.
