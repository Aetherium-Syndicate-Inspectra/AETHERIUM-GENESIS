import pytest
from unittest.mock import MagicMock, patch
import sys
import torch as real_torch

from src.backend.genesis_core import (
    PhysicsIntentData,
    BioSensoryData,
    MemoryDAG,
    ReflexSignal,
    ReflexType,
    NirodhaState
)

def test_physics_intent_data_initialization():
    with patch("src.backend.genesis_core.dna.torch") as mock_torch:
        mock_tensor = MagicMock()
        mock_torch.tensor.return_value = mock_tensor
        # Ensure isinstance check passes or fails gracefully in mock
        # We don't need to mock torch.Tensor because our code handles mocks now

        # Test default initialization
        intent = PhysicsIntentData()
        assert intent.uPulse == 0.0
        assert intent.uChaos == 0.0

        # Test custom initialization
        custom_list = [1.0, 0.5, 0.0]
        intent_custom = PhysicsIntentData(uPulse=1.0, uChaos=0.5, uColor=custom_list)
        assert intent_custom.uPulse == 1.0

def test_bio_sensory_data():
    with patch("src.backend.genesis_core.dna.torch") as mock_torch:
        mock_empty = MagicMock()
        mock_torch.empty.return_value = mock_empty

        bio_data = BioSensoryData()
        # Check that it uses the factory defaults
        assert bio_data.raw_intensity == mock_empty
        assert bio_data.temporal_flow == mock_empty

def test_memory_dag_evolution():
    dag = MemoryDAG()

    # Initial Commit
    hash1 = dag.commit(message="Initial Thought", data={"intent": "wake_up"})
    assert hash1 in dag.commits
    assert dag.heads["main"] == hash1

    # Second Commit
    hash2 = dag.commit(message="Second Thought", data={"intent": "perceive"})
    assert dag.commits[hash2].parent_hash == hash1

def test_reflex_signal():
    reflex = ReflexSignal(signal_type=ReflexType.DEFENSIVE, intensity=0.9)
    assert reflex.signal_type == ReflexType.DEFENSIVE
    assert reflex.intensity == 0.9

def test_nirodha_state():
    state = NirodhaState(is_maintenance_active=True, input_gate_closed=True)
    assert state.is_maintenance_active
    assert state.input_gate_closed
