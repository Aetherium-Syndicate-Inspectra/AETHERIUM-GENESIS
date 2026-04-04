from datetime import datetime, timezone
from uuid import uuid4

from src.backend.genesis_core.entropy.ledger import AkashicTreasury
from src.backend.genesis_core.entropy.schemas import EntropyAssessment, MeterState
from src.backend.genesis_core.models.visual import (
    CognitiveMetadata,
    ContractIntentCategory,
    EmbodimentContract,
    IntentData,
    TemporalPhase,
    TemporalState,
)


def test_entropy_ledger_timestamps_are_utc_timezone_aware():
    treasury = AkashicTreasury()
    assessment = EntropyAssessment(
        packet_id=uuid4(),
        qou_score=0.5,
        semantic_weight=0.5,
        safety_weight=0.9,
        surprise_factor=0.5,
        reward_amount=5,
        meter_state=MeterState.DIVERGENT,
        preserve=False,
    )

    entry = treasury.append(user_id=uuid4(), assessment=assessment, artifact_ref=None)

    assert entry.created_at.tzinfo == timezone.utc


def test_embodiment_contract_default_timestamp_is_utc_isoformat():
    contract = EmbodimentContract(
        temporal_state=TemporalState(phase=TemporalPhase.IDLE, stability=1.0, duration_ms=0),
        cognitive=CognitiveMetadata(effort=0.1, uncertainty=0.1, latency_factor=0.0),
        intent=IntentData(category=ContractIntentCategory.CHIT_CHAT, purity=0.9),
    )

    parsed = datetime.fromisoformat(contract.timestamp)
    assert parsed.tzinfo == timezone.utc
