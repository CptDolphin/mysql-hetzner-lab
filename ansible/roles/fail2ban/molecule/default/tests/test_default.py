"""Testinfra — rola fail2ban: pakiet, jaile (sshd + recidive), autostart."""


def test_fail2ban_installed(host):
    assert host.package("fail2ban").is_installed


def test_jail_local(host):
    f = host.file("/etc/fail2ban/jail.local")
    assert f.exists
    assert "[sshd]" in f.content_string
    assert "[recidive]" in f.content_string
    assert "nftables-multiport" in f.content_string


def test_fail2ban_enabled(host):
    assert host.service("fail2ban").is_enabled
