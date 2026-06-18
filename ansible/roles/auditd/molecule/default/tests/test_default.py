"""Testinfra — rola auditd: pakiet, reguły, retencja, autostart."""


def test_auditd_installed(host):
    assert host.package("auditd").is_installed


def test_audit_rules(host):
    f = host.file("/etc/audit/rules.d/99-lab.rules")
    assert f.exists
    assert "-w /etc/sudoers" in f.content_string
    assert "execve" in f.content_string


def test_auditd_retention(host):
    conf = host.file("/etc/audit/auditd.conf").content_string
    assert "max_log_file = 50" in conf
    assert "max_log_file_action = ROTATE" in conf


def test_auditd_enabled(host):
    assert host.service("auditd").is_enabled
