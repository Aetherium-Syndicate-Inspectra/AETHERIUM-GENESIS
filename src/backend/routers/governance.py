from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel

from src.backend.genesis_core.governance.core import ApprovalRequest
from src.backend.genesis_core.lifecycle import LifecycleManager
from src.backend.genesis_core.memory.akashic import MemoryProjectionManager

router = APIRouter(prefix="/governance", tags=["governance"])

lifecycle = LifecycleManager()
memory_projection = MemoryProjectionManager(lifecycle.ledger)


@router.get("/approvals", response_model=List[ApprovalRequest])
async def get_pending_approvals():
    gov = lifecycle.validator.governance
    return list(gov.pending_approvals.values())


class ApprovalDecision(BaseModel):
    request_id: str
    decision: str  # APPROVED or REJECTED


@router.post("/decide")
async def handle_decision(decision: ApprovalDecision):
    gov = lifecycle.validator.governance
    success = gov.handle_approval(decision.request_id, decision.decision)
    if not success:
        raise HTTPException(status_code=404, detail="Request not found")
    return {"status": "success", "decision": decision.decision}


@router.get("/gems")
async def get_gems() -> Dict[str, Any]:
    gem_projection = memory_projection.get_gem_projection()
    gems = [entry["current"] for entry in gem_projection.get("gems", {}).values() if "current" in entry]
    return {"gems": gems}


class GemSimulationRequest(BaseModel):
    gem: Dict[str, Any]
    shadow_mode: bool = True


@router.post("/simulate-policy")
async def simulate_policy(request: GemSimulationRequest):
    gov = lifecycle.validator.governance
    return gov.simulate_rule_promotion(gem=request.gem, shadow_mode=request.shadow_mode)
