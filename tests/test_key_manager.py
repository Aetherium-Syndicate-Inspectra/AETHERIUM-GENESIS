from src.backend.security.key_manager import KeyStoreData


def test_keystoredata_uses_independent_key_maps():
    first = KeyStoreData()
    second = KeyStoreData()

    assert first.keys is not second.keys

    first.keys["ak-test"] = "sentinel"

    assert "ak-test" in first.keys
    assert "ak-test" not in second.keys
