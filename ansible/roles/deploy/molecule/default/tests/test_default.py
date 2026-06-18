"""Testinfra — rola deploy: katalog + prod-compose + .env (poprawne wartości i uprawnienia)."""


def test_app_dir(host):
    d = host.file("/opt/mysql-lab-app")
    assert d.is_directory
    assert d.mode == 0o750


def test_compose_rendered(host):
    f = host.file("/opt/mysql-lab-app/docker-compose.prod.yml")
    assert f.exists
    assert "ghcr.io/cptdolphin/mysql-hetzner-lab-app" in f.content_string
    assert "127.0.0.1:8000:8000" in f.content_string   # tylko dla nginx na hoście
    assert "read_only: true" in f.content_string
    assert "no-new-privileges:true" in f.content_string


def test_env_rendered(host):
    f = host.file("/opt/mysql-lab-app/.env")
    assert f.exists
    assert f.mode == 0o600
    assert "DB_HOST=127.0.0.1" in f.content_string
    assert "DB_PORT=6033" in f.content_string   # przez ProxySQL
    assert "DB_USER=appuser" in f.content_string
