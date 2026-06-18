"""Testinfra — rola proxysql: instalacja, usługa, porty admin/proxy, backend + user w configu."""

ADMIN = "mysql -h127.0.0.1 -P6032 -uadmin -padmin -N -B -e"


def test_proxysql_installed(host):
    assert host.package("proxysql").is_installed


def test_proxysql_running(host):
    assert host.service("proxysql").is_running


def test_ports_listening(host):
    # sprawdzamy nasłuch portów niezależnie od bind-addr (admin 0.0.0.0:6032)
    listening = host.check_output("ss -tlnH")
    assert ":6032" in listening  # admin interface
    assert ":6033" in listening  # proxy (klienci aplikacji)


def test_backend_configured(host):
    out = host.run(f'{ADMIN} "SELECT hostname,port FROM mysql_servers"')
    assert "127.0.0.1" in out.stdout
    assert "3306" in out.stdout


def test_app_user_configured(host):
    out = host.run(f'{ADMIN} "SELECT username FROM mysql_users"')
    assert "appuser" in out.stdout
