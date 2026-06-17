# ADR-0002 — Silnik backupu: Percona XtraBackup + binlog (PITR)

- **Status:** zaakceptowany
- **Kontekst:** wymagany backup pełny + **point-in-time recovery**, na „produkcyjnym" poziomie i jako materiał do nauki.

## Decyzja
**Percona XtraBackup 8.0** (fizyczny, hot, nieblokujący) na pełny backup + **ciągła archiwizacja binlogów** na PITR.
Szyfrowanie przed wysyłką, offsite na Storage Box ([backup-and-recovery.md](../explanation/backup-and-recovery.md)).

## Konsekwencje
- (+) Backup bez blokad na żywej bazie; inkrementalne; szybki restore dużych zbiorów; realny, „produkcyjny" mechanizm.
- (−) Więcej konfiguracji niż `mysqldump`; wymaga zgodnej wersji do MySQL 8.0 i pilnowania binlogów.
- Wymusza `log_bin`/`ROW` i jawne RPO/RTO + obowiązkowe drille.

## Alternatywy odrzucone
- **`mysqldump --single-transaction`** — prostszy, ale wolny restore i większy narzut przy dużych bazach; słabszy sygnał „prod". (Zostaje jako awaryjny dump.)
- **Snapshot zarządzany / Volume snapshot** — nie uczy mechanizmu i nie daje spójnego PITR na poziomie transakcji.
