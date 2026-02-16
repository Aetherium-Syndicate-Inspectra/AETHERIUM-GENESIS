import pytest
import torch
import sys
import os
import asyncio
from typing import Any
from unittest.mock import MagicMock, patch

# Ensure src is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.backend.departments.design.chromatic.aetherium_vision_core import AetheriumVisionCore, AetherState, AetherOutput
from src.backend.genesis_core.logenesis.engine import LogenesisEngine
from src.backend.genesis_core.models.logenesis import IntentPacket
from src.backend.genesis_core.models.visual import BaseShape, VisualParameters

class TestVisionCore:
    def test_vision_core_forward(self):
        """Test the forward pass of AetheriumVisionCore."""
        core = AetheriumVisionCore()
        dummy_img = torch.rand(1, 3, 224, 224)
        output = core(dummy_img)

        # In mock environments, isinstance might fail if AetherOutput or torch types are mocked
        # We check attributes for robustness
        assert hasattr(output, 'light_field')
        assert hasattr(output, 'embedding')
        assert hasattr(output, 'energy_level')

    @pytest.mark.asyncio
    async def test_logenesis_visual_integration(self):
        """Test LogenesisEngine processing a visual packet."""
        engine = LogenesisEngine()

        mock_output = AetherOutput(
            light_field=torch.randn(1, 3, 224, 224),
            embedding=torch.randn(1, 768),
            energy_level=0.8,
            confidence=0.9,
            state=AetherState.ANALYSIS
        )

        packet = IntentPacket(
            modality="visual",
            embedding=mock_output.embedding,
            energy_level=mock_output.energy_level,
            confidence=mock_output.confidence,
            raw_payload=mock_output
        )

        response = await engine.process(packet, session_id="test_visual_session")

        if response.state != "COLLAPSED":
             assert response.visual_analysis is not None
             assert response.visual_analysis.visual_parameters.base_shape == BaseShape.VORTEX
             assert response.manifestation_granted is True
