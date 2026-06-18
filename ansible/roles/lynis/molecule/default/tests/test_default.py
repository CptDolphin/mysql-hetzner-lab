"""Testinfra — rola lynis: pakiet, katalog raportów, miesięczny cron z progiem."""


def test_lynis_installed(host):
    assert host.package("lynis").is_installed


def test_report_dir(host):
    d = host.file("/var/log/lynis-audits")
    assert d.is_directory
    assert d.mode == 0o750


def test_monthly_cron(host):
    f = host.file("/etc/cron.monthly/lynis-audit")
    assert f.exists
    assert f.mode == 0o755
    assert "hardening_index" in f.content_string
    assert "lynis audit system" in f.content_string
