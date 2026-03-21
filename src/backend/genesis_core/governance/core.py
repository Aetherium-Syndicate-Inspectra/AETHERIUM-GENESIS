"""Deprecated compatibility shim for governance runtime.

Canonical runtime governance now lives under ``src.backend.governance.*``.
Keep imports here only for legacy compatibility paths while migrating callers.
Do not add new business logic to this module.
"""

from src.backend.governance.core import (
    ApprovalDecisionResult,
    ApprovalRequest,
    GovernanceCore,
)
from src.backend.governance.risk_tiering import ActionTier

__all__ = [
    "ActionTier",
    "ApprovalDecisionResult",
    "ApprovalRequest",
    "GovernanceCore",
]
