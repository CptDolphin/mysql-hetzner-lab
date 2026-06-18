"""Testinfra — rola nftables: pakiet, ruleset (default-deny + porty), walidacja, autostart."""


def test_nftables_installed(host):
    assert host.package("nftables").is_installed


def test_ruleset_file(host):
    f = host.file("/etc/nftables.conf")
    assert f.exists
    assert "policy drop" in f.content_string
    assert "tcp dport 22" in f.content_string
    assert "tcp dport { 80, 443 }" in f.content_string
    # limity PER-IP (nie globalne) — kluczowe dla obrony przed pojedynczym atakującym IP
    assert "meter web-conn" in f.content_string
    assert "meter web-rate" in f.content_string
    # named-set czarnej listy — ręczne bany IP/CIDR przeżywają reload reguł (runbook under-attack 2A)
    assert "set blackhole" in f.content_string
    assert "ip saddr @blackhole drop" in f.content_string
    assert "ip6 saddr @blackhole6 drop" in f.content_string


def test_ruleset_syntax_valid(host):
    # nft -c = dry-run check składni ruleset (bez ładowania)
    assert host.run("nft -c -f /etc/nftables.conf").rc == 0


def test_nftables_enabled(host):
    assert host.service("nftables").is_enabled
