"""Testinfra — rola backup: XtraBackup, user, skrypt, timer + REALNY backup (integracja)."""


def test_xtrabackup_installed(host):
    assert host.exists("xtrabackup")


def test_backup_user_exists(host):
    out = host.run("mysql -N -B -e \"SELECT user FROM mysql.user WHERE user='xtrabackup'\"")
    assert "xtrabackup" in out.stdout


def test_backup_script(host):
    f = host.file("/usr/local/bin/mysql-backup.sh")
    assert f.exists
    assert f.mode == 0o750


def test_backup_timer_enabled(host):
    assert host.service("mysql-backup.timer").is_enabled


def test_backup_actually_runs(host):
    # uruchom pełny backup i sprawdź, że powstał PRZYGOTOWANY backup (xtrabackup_checkpoints)
    res = host.run("/usr/local/bin/mysql-backup.sh")
    assert res.rc == 0, res.stderr
    cp = host.run("find /var/backups/mysql -name xtrabackup_checkpoints")
    assert cp.stdout.strip() != ""
