"""Testinfra — przykładowe asercje. Dopisz właściwe per rola (serwis/port/config/user)."""


def test_host_is_ubuntu(host):
    assert host.system_info.distribution.lower() in ("ubuntu", "debian")


# Przykłady do skopiowania w rolach:
# def test_service_running(host):
#     svc = host.service("mysql")
#     assert svc.is_running and svc.is_enabled
#
# def test_port_listening_localhost_only(host):
#     s = host.socket("tcp://127.0.0.1:3306")
#     assert s.is_listening
#     assert not host.socket("tcp://0.0.0.0:3306").is_listening
