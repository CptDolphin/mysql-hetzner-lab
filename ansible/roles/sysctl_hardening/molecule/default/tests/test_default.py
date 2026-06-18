"""Testinfra — rola sysctl_hardening: plik CIS z kluczowymi wartościami."""


def test_sysctl_file(host):
    f = host.file("/etc/sysctl.d/99-hardening.conf")
    assert f.exists
    assert f.mode == 0o644
    for line in (
        "net.ipv4.tcp_syncookies = 1",
        "net.ipv4.conf.all.rp_filter = 1",
        "kernel.kptr_restrict = 2",
        "fs.suid_dumpable = 0",
        "net.core.bpf_jit_harden = 2",
    ):
        assert line in f.content_string
