"""Testinfra — rola rkhunter: pakiety, config, cotygodniowy skan."""


def test_packages(host):
    assert host.package("rkhunter").is_installed
    assert host.package("chkrootkit").is_installed


def test_conf_local(host):
    f = host.file("/etc/rkhunter.conf.local")
    assert f.exists
    assert "WEB_CMD=/usr/bin/wget" in f.content_string
    assert "DISABLE_TESTS" in f.content_string


def test_weekly_scan(host):
    f = host.file("/etc/cron.weekly/rootkit-scan")
    assert f.exists
    assert f.mode == 0o755
    assert "rkhunter --cronjob" in f.content_string
