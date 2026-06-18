"""Testinfra — rola swap: plik utworzony, sformatowany, wpis w fstab."""


def test_swapfile_exists(host):
    f = host.file("/swapfile")
    assert f.exists
    assert f.mode == 0o600


def test_swapfile_is_swap(host):
    assert "swap" in host.check_output("file -bs /swapfile")


def test_fstab_entry(host):
    fstab = host.file("/etc/fstab").content_string
    assert "/swapfile" in fstab
    assert "swap" in fstab
