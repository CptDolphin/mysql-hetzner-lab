"""Testinfra — rola common: pakiety bazowe + strefa czasowa."""


def test_base_packages_installed(host):
    for pkg in ("git", "jq", "curl", "htop", "ca-certificates"):
        assert host.package(pkg).is_installed, f"{pkg} powinien być zainstalowany"


def test_timezone_set(host):
    # community.general.timezone ustawia symlink /etc/localtime (oba backendy)
    assert host.check_output("readlink -f /etc/localtime").endswith("Europe/Warsaw")
