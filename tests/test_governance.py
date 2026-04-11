import unittest
from src.backend.governance.core import GovernanceCore, ApprovalRequest
from src.backend.governance.risk_tiering import ActionTier
from src.backend.genesis_core.agents.validator import ValidatorAgent
from src.backend.genesis_core.models.intent import SystemIntent, IntentPayload, IntentContext

class TestGovernance(unittest.TestCase):
    def setUp(self):
        self.gov = GovernanceCore(config={"auto_approve_tier_1": False})
        self.validator = ValidatorAgent(governance=self.gov)

    def test_risk_assessment(self):
        self.assertEqual(self.gov.assess_risk("read_file", {}), ActionTier.TIER_0_READ_ONLY)
        self.assertEqual(self.gov.assess_risk("update_document", {}), ActionTier.TIER_1_REVERSIBLE_LOW_RISK)
        self.assertEqual(self.gov.assess_risk("send_email", {}), ActionTier.TIER_2_EXTERNAL_IMPACT)
        self.assertEqual(self.gov.assess_risk("delete_all_data", {}), ActionTier.TIER_3_SENSITIVE_IRREVERSIBLE)

    def test_validator_gating(self):
        # Tier 2 action should be gated
        payload = IntentPayload(content={"action": "send_email", "to": "test@example.com"}, modality="json")
        intent = SystemIntent(
            origin_agent="AgioSage",
            intent_type="EXECUTION_REQUEST",
            payload=payload,
            context=IntentContext()
        )

        allowed = self.validator.audit_gate(intent)
        self.assertFalse(allowed)
        self.assertEqual(len(self.gov.pending_approvals), 1)

    def test_approval_flow(self):
        payload = IntentPayload(content={"action": "send_email"}, modality="json")
        intent = SystemIntent(origin_agent="AgioSage", intent_type="EXECUTION_REQUEST", payload=payload, context=IntentContext())

        self.validator.audit_gate(intent)
        req_id = list(self.gov.pending_approvals.keys())[0]

        result = self.gov.handle_approval(req_id, "APPROVED")
        self.assertEqual(result.status, "APPROVED")
        self.assertEqual(result.decision, "APPROVED")
        self.assertEqual(self.gov.pending_approvals[req_id].status, "APPROVED")

    def test_rejected_approval_is_not_not_found(self):
        payload = IntentPayload(content={"action": "send_email"}, modality="json")
        intent = SystemIntent(origin_agent="AgioSage", intent_type="EXECUTION_REQUEST", payload=payload, context=IntentContext())

        self.validator.audit_gate(intent)
        req_id = list(self.gov.pending_approvals.keys())[0]

        result = self.gov.handle_approval(req_id, "REJECTED")

        self.assertEqual(result.status, "REJECTED")
        self.assertEqual(result.request_id, req_id)
        self.assertNotEqual(result.status, "NOT_FOUND")

    def test_unknown_approval_request_returns_not_found_status(self):
        result = self.gov.handle_approval("missing-request", "APPROVED")

        self.assertEqual(result.status, "NOT_FOUND")
        self.assertEqual(result.decision, "APPROVED")

if __name__ == '__main__':
    unittest.main()
