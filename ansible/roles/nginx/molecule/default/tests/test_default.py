"""Testinfra — rola nginx: instalacja, config waliduje się, rate-limit + proxy, usługa + porty."""


def test_nginx_installed(host):
    assert host.package("nginx").is_installed


def test_config_valid(host):
    assert host.run("nginx -t").rc == 0


def test_ratelimit_zone(host):
    f = host.file("/etc/nginx/conf.d/00-ratelimit.conf")
    assert f.exists
    assert "limit_req_zone" in f.content_string


def test_proxy_and_limits(host):
    f = host.file("/etc/nginx/conf.d/app.conf")
    assert f.exists
    assert "proxy_pass" in f.content_string
    assert "limit_req zone=applimit" in f.content_string
    assert "ssl_certificate" in f.content_string


def test_running_and_ports(host):
    assert host.service("nginx").is_running
    listening = host.check_output("ss -tlnH")
    assert ":80" in listening
    assert ":443" in listening
