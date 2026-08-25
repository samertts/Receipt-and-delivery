from lab_system.app.updater import is_startup_check_enabled


def test_startup_update_check_requires_windows_and_public_key():
    assert not is_startup_check_enabled("posix", "configured-key")
    assert not is_startup_check_enabled("nt", "")
    assert is_startup_check_enabled("nt", "configured-key")
