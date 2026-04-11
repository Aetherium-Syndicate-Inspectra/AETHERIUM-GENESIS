import json
import uuid

from fastapi.testclient import TestClient

from src.backend.main import app
from src.backend.governance.core import ApprovalRequest
from src.backend.governance.risk_tiering import ActionTier
from src.backend.genesis_core.memory.akashic import AkashicRecords


def test_governance_decide_distinguishes_rejected_from_not_found(tmp_path):
    with TestClient(app) as client:
        ledger = AkashicRecords(db_path=str(tmp_path / "akashic.json"))
        governance = app.state.governance
        governance.ledger = ledger

        request_id = str(uuid.uuid4())
        governance.request_approval(
            ApprovalRequest(
                request_id=request_id,
                tier=ActionTier.TIER_2_EXTERNAL_IMPACT,
                actor="tester",
                intent_id="intent-1",
                action_type="send_email",
                resource="customer.outbound",
                preview_data={"real_world": True},
            )
        )

        rejected = client.post("/governance/decide", json={"request_id": request_id, "decision": "REJECTED"})
        assert rejected.status_code == 200
        assert rejected.json()["status"] == "REJECTED"
        assert rejected.json()["approval_status"] == "REJECTED"
        assert rejected.json()["request_id"] == request_id

        not_found = client.post("/governance/decide", json={"request_id": "missing", "decision": "APPROVED"})
        assert not_found.status_code == 404
        assert not_found.json()["detail"]["status"] == "NOT_FOUND"
        assert "not found" in not_found.json()["detail"]["detail"].lower()

        chain = json.loads((tmp_path / "akashic.json").read_text())["chain"]
        assert chain[-1]["payload"]["decision_status"] == "REJECTED"
        assert chain[-1]["payload"]["type"] == "approval_decided"


def test_governance_approvals_endpoint_uses_canonical_runtime_state(tmp_path):
    with TestClient(app) as client:
        governance = app.state.governance
        governance.ledger = AkashicRecords(db_path=str(tmp_path / "akashic.json"))
        request_id = str(uuid.uuid4())
        governance.request_approval(
            ApprovalRequest(
                request_id=request_id,
                tier=ActionTier.TIER_2_EXTERNAL_IMPACT,
                actor="tester",
                intent_id="intent-2",
                action_type="send_email",
                resource="customer.outbound",
                preview_data={"real_world": True},
            )
        )

        response = client.get("/governance/approvals")
        assert response.status_code == 200
        approvals = response.json()
        assert any(item["request_id"] == request_id and item["status"] == "PENDING_APPROVAL" for item in approvals)
