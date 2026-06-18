"""Testinfra — rola unattended_upgrades: pakiet, config security-only, timery."""


def test_package_installed(host):
    assert host.package("unattended-upgrades").is_installed


def test_periodic_enabled(host):
    f = host.file("/etc/apt/apt.conf.d/20auto-upgrades")
    assert f.exists
    assert 'APT::Periodic::Unattended-Upgrade "1"' in f.content_string


def test_no_automatic_reboot(host):
    f = host.file("/etc/apt/apt.conf.d/50unattended-upgrades")
    assert 'Unattended-Upgrade::Automatic-Reboot "false"' in f.content_string


def test_apt_daily_timers_enabled(host):
    for timer in ("apt-daily.timer", "apt-daily-upgrade.timer"):
        assert host.service(timer).is_enabled
