"""Testinfra — rola swap: plik utworzony, sformatowany, wpis w fstab."""


def test_swapfile_exists(host):
    f = host.file("/swapfile")
    assert f.exists
    assert f.mode == 0o600


def test_swapfile_is_swap(host):
    # mkswap zapisuje sygnaturę "SWAPSPACE2" w nagłówku — bez zależności od `file`
    assert host.run("grep -aq SWAPSPACE2 /swapfile").rc == 0


def test_fstab_entry(host):
    fstab = host.file("/etc/fstab").content_string
    assert "/swapfile" in fstab
    assert "swap" in fstab
