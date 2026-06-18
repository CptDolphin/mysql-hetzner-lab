"""Testinfra — rola mysql: instalacja, bind localhost, binlog ROW, least-priv user."""


def test_mysql_installed(host):
    assert host.package("mysql-server").is_installed


def test_config_bind_localhost(host):
    f = host.file("/etc/mysql/mysql.conf.d/99-lab.cnf")
    assert f.exists
    assert "bind-address = 127.0.0.1" in f.content_string
    assert "binlog_format = ROW" in f.content_string


def test_mysql_running(host):
    assert host.service("mysql").is_running


def test_binlog_enabled_row(host):
    log_bin = host.check_output("mysql -N -B -e \"SHOW VARIABLES LIKE 'log_bin'\"")
    fmt = host.check_output("mysql -N -B -e \"SHOW VARIABLES LIKE 'binlog_format'\"")
    assert "ON" in log_bin
    assert "ROW" in fmt


def test_not_listening_publicly(host):
    assert host.socket("tcp://127.0.0.1:3306").is_listening
    assert not host.socket("tcp://0.0.0.0:3306").is_listening


def test_app_user_least_priv(host):
    user = host.check_output(
        "mysql -N -B -e \"SELECT user FROM mysql.user WHERE user='appuser' AND host='127.0.0.1'\""
    )
    assert "appuser" in user
    # brak uprawnień DROP/ALL — tylko CRUD na appdb
    grants = host.check_output("mysql -N -B -e \"SHOW GRANTS FOR 'appuser'@'127.0.0.1'\"")
    assert "SELECT, INSERT, UPDATE, DELETE" in grants
    assert "ALL PRIVILEGES" not in grants
