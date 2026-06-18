"""Testinfra — PITR-drill: dowód odzysku do punktu w czasie.

Cykl: insert A -> backup -> insert B (czas T1) -> insert C -> DROP ->
restore pełny + replay binlogów do T1 -> weryfikacja: A i B są, C NIE.
"""

import time


def _sql(host, query):
    return host.run('mysql -N -B -e "%s"' % query)


def test_restore_script_present(host):
    f = host.file("/usr/local/bin/mysql-restore.sh")
    assert f.exists
    assert f.mode == 0o750


def test_pitr_drill(host):
    # 1. tabela + wiersz A
    _sql(host, "CREATE DATABASE IF NOT EXISTS drilldb")
    _sql(host, "CREATE TABLE drilldb.t (id INT PRIMARY KEY, v VARCHAR(8))")
    _sql(host, "INSERT INTO drilldb.t VALUES (1,'A')")

    # 2. pełny backup (zawiera A)
    host.run("rm -rf /var/backups/mysql/20*")
    b = host.run("/usr/local/bin/mysql-backup.sh")
    assert b.rc == 0, b.stderr

    # 3. wiersz B, punkt w czasie T1, wiersz C
    _sql(host, "INSERT INTO drilldb.t VALUES (2,'B')")
    time.sleep(2)
    t1 = host.check_output("date -u '+%Y-%m-%d %H:%M:%S'")
    time.sleep(2)
    _sql(host, "INSERT INTO drilldb.t VALUES (3,'C')")

    # 4. archiwizacja binlogów (domyka binlog z B i C)
    a = host.run("/usr/local/bin/mysql-binlog-archive.sh")
    assert a.rc == 0, a.stderr

    # 5. katastrofa
    _sql(host, "DROP TABLE drilldb.t")

    # 6. restore pełny + PITR do T1
    backup_path = host.check_output("ls -d /var/backups/mysql/20* | sort | tail -1")
    r = host.run("/usr/local/bin/mysql-restore.sh '%s' '%s'" % (backup_path, t1))
    assert r.rc == 0, r.stderr

    # 7. dowód: A i B odzyskane, C (po T1) NIE
    rows = host.check_output('mysql -N -B -e "SELECT v FROM drilldb.t ORDER BY id"')
    assert "A" in rows, rows
    assert "B" in rows, rows
    assert "C" not in rows, rows
