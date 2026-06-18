"""Testinfra — rola chrony: pakiet, config, usługa działa, timesyncd wyłączony."""


def test_chrony_installed(host):
    assert host.package("chrony").is_installed


def test_chrony_config(host):
    f = host.file("/etc/chrony/conf.d/99-lab.conf")
    assert f.exists
    assert "pool" in f.content_string
    assert "makestep" in f.content_string


def test_chrony_running(host):
    s = host.service("chrony")
    assert s.is_running
    assert s.is_enabled
