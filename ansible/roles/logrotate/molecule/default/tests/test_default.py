"""Testinfra — rola logrotate: configi docker/caddy + limit journald."""


def test_logrotate_installed(host):
    assert host.package("logrotate").is_installed


def test_docker_logrotate(host):
    f = host.file("/etc/logrotate.d/docker")
    assert f.exists
    assert "copytruncate" in f.content_string


def test_caddy_logrotate(host):
    assert host.file("/etc/logrotate.d/caddy").exists


def test_journald_limit(host):
    f = host.file("/etc/systemd/journald.conf.d/99-lab.conf")
    assert f.exists
    assert "SystemMaxUse=1G" in f.content_string
