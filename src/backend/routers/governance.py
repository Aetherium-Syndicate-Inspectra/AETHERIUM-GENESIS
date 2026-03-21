from fastapi import APIRouter, HTTPException, Request
from typing import List, Dict, Any
from pydantic import BaseModel
import logging

from src.backend.governance.core import ApprovalDecisionResult, ApprovalRequest, GovernanceCore
from src.backend.genesis_core.governance.scenario_presets import (
    get_scenario_preset,
    list_scenario_presets,
)
from src.backend.genesis_core.lifecycle import LifecycleManager
from src.backend.genesis_core.memory.akashic import MemoryProjectionManager

router = APIRouter(prefix="/governance", tags=["governance"])
logger = logging.getLogger("governance.router")

lifecycle = LifecycleManager()
memory_projection = MemoryProjectionManager(lifecycle.ledger)


def _governance_from_request(request: Request) -> GovernanceCore:
    return getattr(request.app.state, "governance", lifecycle.validator.governance)


@router.get("/approvals", response_model=List[ApprovalRequest])
async def get_pending_approvals(request: Request):
    gov = _governance_from_request(request)
    return [
        ApprovalRequest(
            request_id=ticket.ticket_id,
            tier=ticket.risk_tier,
            actor="governance",
            intent_id=ticket.ticket_id,
            action_type=ticket.action,
            resource=ticket.resource,
            preview_data={"impact": ticket.impact, "evidence": ticket.evidence},
            status=ticket.status,
            created_at=ticket.created_at,
        )
        for ticket in gov.list_pending_approvals()
    ]


class ApprovalDecision(BaseModel):
    request_id: str
    decision: str  # APPROVED or REJECTED


@router.post("/decide")
async def handle_decision(decision: ApprovalDecision, request: Request):
    gov = _governance_from_request(request)
    result: ApprovalDecisionResult = gov.handle_approval(decision.request_id, decision.decision)
    if result.status == "NOT_FOUND":
        raise HTTPException(
            status_code=404,
            detail={
                "status": "NOT_FOUND",
                "request_id": result.request_id,
                "decision": result.decision,
                "detail": result.detail,
            },
        )
    return {
        "status": result.status,
        "approval_status": result.status,
        "request_id": result.request_id,
        "decision": result.decision,
        "detail": result.detail,
    }


@router.get("/gems")
async def get_gems() -> Dict[str, Any]:
    gem_projection = memory_projection.get_gem_projection()
    gems = [entry["current"] for entry in gem_projection.get("gems", {}).values() if "current" in entry]
    return {"gems": gems}


class GemSimulationRequest(BaseModel):
    gem: Dict[str, Any]
    shadow_mode: bool = True


@router.post("/simulate-policy")
async def simulate_policy(request: GemSimulationRequest, http_request: Request):
    gov = _governance_from_request(http_request)
    return gov.simulate_rule_promotion(gem=request.gem, shadow_mode=request.shadow_mode)


@router.get("/scenario-presets")
async def get_scenario_presets() -> Dict[str, List[Dict[str, Any]]]:
    return {"presets": list_scenario_presets()}


class ScenarioPresetRunRequest(BaseModel):
    preset_id: str


@router.post("/scenario-presets/run")
async def run_scenario_preset(request: ScenarioPresetRunRequest, http_request: Request) -> Dict[str, Any]:
    gov = _governance_from_request(http_request)
    try:
        preset = get_scenario_preset(request.preset_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    logger.info("Running governance scenario preset", extra={"preset_id": preset.preset_id})
    results: List[Dict[str, Any]] = []
    for scenario_action in preset.actions:
        tier = gov.assess_risk(action_type=scenario_action.action_type, payload=scenario_action.payload)
        status = "PENDING_APPROVAL" if int(tier) >= 2 else "ALLOWED"
        results.append(
            {
                "action_type": scenario_action.action_type,
                "tier": int(tier),
                "status": status,
            }
        )

    return {
        "preset_id": preset.preset_id,
        "name": preset.name,
        "actions": results,
        "summary": {
            "total": len(results),
            "approval_required": len([r for r in results if r["status"] == "PENDING_APPROVAL"]),
        },
    }
