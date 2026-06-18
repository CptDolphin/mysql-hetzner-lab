"""Testinfra — rola swap: plik utworzony, sformatowany, wpis w fstab.

Ścieżka molecule = /swapfile-molecule (nie /swapfile — koliduje ze swapem runnera).
"""

SWAP = "/swapfile-molecule"


def test_swapfile_exists(host):
    f = host.file(SWAP)
    assert f.exists
    assert f.mode == 0o600


def test_swapfile_is_swap(host):
    # mkswap zapisuje sygnaturę "SWAPSPACE2" w nagłówku — bez zależności od `file`
    assert host.run(f"grep -aq SWAPSPACE2 {SWAP}").rc == 0


def test_fstab_entry(host):
    fstab = host.file("/etc/fstab").content_string
    assert SWAP in fstab
    assert "swap" in fstab
