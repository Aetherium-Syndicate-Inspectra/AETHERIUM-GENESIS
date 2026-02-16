from src.backend.genesis_core.memory.akashic import AkashicRecords


def test_json_backend_isolated_tenants(tmp_path):
    db_path = tmp_path / "akashic.json"
    akashic = AkashicRecords(db_path=str(db_path), backend="json")

    akashic.append_record({"actor": "user-1", "action": "PING"}, tenant_id="tenant-a")
    akashic.append_record({"actor": "user-2", "action": "PING"}, tenant_id="tenant-b")

    a_history = akashic.get_behavioral_history("user-1", tenant_id="tenant-a")
    b_history = akashic.get_behavioral_history("user-2", tenant_id="tenant-b")
    leak_check = akashic.get_behavioral_history("user-1", tenant_id="tenant-b")

    assert len(a_history) == 1
    assert len(b_history) == 1
    assert leak_check == []


def test_backward_compatible_global_chain(tmp_path):
    db_path = tmp_path / "legacy_akashic.json"
    db_path.write_text('{"chain": []}', encoding="utf-8")

    akashic = AkashicRecords(db_path=str(db_path), backend="json")
    akashic.append_record({"actor": "legacy", "action": "WRITE"})

    assert akashic.verify_hash_chain()
    assert akashic.check_temporal_consistency()
