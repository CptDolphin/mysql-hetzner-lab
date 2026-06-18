"""Testinfra — rola sshd_lockdown: config hardeningu + efektywne wartości sshd."""


def test_openssh_installed(host):
    assert host.package("openssh-server").is_installed


def test_hardening_dropin(host):
    f = host.file("/etc/ssh/sshd_config.d/10-hardening.conf")
    assert f.exists
    for directive in (
        "PermitRootLogin no",
        "PasswordAuthentication no",
        "AuthenticationMethods publickey",
        "AllowTcpForwarding local",
    ):
        assert directive in f.content_string


def test_sshd_config_valid(host):
    # sshd -t = 0 gdy cała efektywna konfiguracja jest poprawna składniowo
    assert host.run("sshd -t").rc == 0


def test_effective_hardening(host):
    # sshd -T dumpuje efektywną konfigurację (nie tylko plik)
    out = host.check_output("sshd -T").lower()
    assert "permitrootlogin no" in out
    assert "passwordauthentication no" in out
