from src.backend.governance.core import GovernanceCore
from src.backend.governance.risk_tiering import ActionTier, RiskTiering
from src.backend.memory.fabric import MemoryFabric


def test_risk_tiering_and_approval_gate():
    governance = GovernanceCore()
    decision = governance.evaluate_action("send_email", "customer.outbound", {"real_world": True})
    assert decision.status == "PENDING_APPROVAL"
    assert decision.risk_tier == ActionTier.TIER_2_EXTERNAL_IMPACT
    assert decision.ticket_id is not None


def test_policy_denies_secret_mutation_in_production():
    governance = GovernanceCore()
    decision = governance.evaluate_action("update_secret", "prod/secret/payment", {"environment": "production"})
    assert decision.status == "DENIED"
    assert decision.recommendation == "suspend"


def test_memory_fabric_projection(tmp_path):
    ledger = tmp_path / "akashic.json"
    ledger.write_text('{"chain": [{"hash": "abc", "timestamp": 1, "payload": {"type": "intent_created"}, "provenance": {"actor": "system"}}]}')
    fabric = MemoryFabric(ledger_path=str(ledger), memory_root=str(tmp_path / "memory"))
    counts = fabric.project()
    assert counts["episodic"] == 1
    assert (tmp_path / "memory" / "episodes" / "abc.json").exists()


def test_classifier_defaults_read_only():
    assert RiskTiering.classify("inspect_status") == ActionTier.TIER_0_READ_ONLY
