"""Testinfra — rola certbot: pakiety, deploy-hook reload nginx, timer auto-renew."""


def test_certbot_installed(host):
    assert host.package("certbot").is_installed
    assert host.package("python3-certbot-nginx").is_installed


def test_deploy_hook(host):
    f = host.file("/etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh")
    assert f.exists
    assert f.mode == 0o755
    assert "systemctl reload nginx" in f.content_string


def test_renewal_timer_enabled(host):
    assert host.service("certbot.timer").is_enabled
