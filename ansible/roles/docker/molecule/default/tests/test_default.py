"""Testinfra — rola docker: klient zainstalowany, daemon.json hardening, autostart."""


def test_docker_client(host):
    assert host.run("docker --version").rc == 0


def test_compose_plugin(host):
    assert host.package("docker-compose-plugin").is_installed


def test_daemon_json_hardening(host):
    f = host.file("/etc/docker/daemon.json")
    assert f.exists
    assert "no-new-privileges" in f.content_string
    assert "json-file" in f.content_string


def test_docker_enabled(host):
    assert host.service("docker").is_enabled
