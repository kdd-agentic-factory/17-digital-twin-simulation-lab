from digital_twin_lab.config import Settings

def test_service_defaults_to_loopback_and_keeps_explicit_container_binding():
    assert Settings(_env_file=None).app_host == "127.0.0.1"
    assert Settings(_env_file=None, app_host="0.0.0.0").app_host == "0.0.0.0"
