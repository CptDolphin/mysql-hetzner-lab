"""Testinfra — rola deploy_user: user + sudo NOPASSWD + .ssh + klucz."""


def test_user_exists_in_sudo(host):
    u = host.user("deploy")
    assert u.exists
    assert u.shell == "/bin/bash"
    assert "sudo" in u.groups


def test_sudoers_nopasswd(host):
    f = host.file("/etc/sudoers.d/deploy")
    assert f.exists
    assert f.mode == 0o440
    assert "NOPASSWD:ALL" in f.content_string


def test_ssh_dir(host):
    d = host.file("/home/deploy/.ssh")
    assert d.is_directory
    assert d.user == "deploy"
    assert d.mode == 0o700


def test_authorized_key_installed(host):
    ak = host.file("/home/deploy/.ssh/authorized_keys")
    assert ak.exists
    assert "ssh-ed25519" in ak.content_string
