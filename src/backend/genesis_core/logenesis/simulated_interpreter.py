from typing import Dict, Any, Optional
from .interpreter import IntentInterpreter
from src.backend.genesis_core.models.visual import (
    EmbodimentContract, TemporalState, CognitiveMetadata, IntentData,
    TemporalPhase, ContractIntentCategory, IntentCategory, VisualSpecifics, BaseShape
)

class SimulatedIntentInterpreter(IntentInterpreter):
    """A deterministic interpreter for testing and fallback scenarios.

    Maps specific keywords to predefined EmbodimentContracts, allowing for consistent
    behavior verification without reliance on external LLM APIs.
    """

    async def interpret(self, text: str, context: Optional[Dict[str, Any]] = None) -> EmbodimentContract:
        """Interprets text using keyword matching to generate a simulated contract.

        Args:
            text: The user input text.
            context: Optional context (unused in simulation).

        Returns:
            A deterministic EmbodimentContract based on input keywords.
        """
        text = text.lower()

        # Defaults
        phase = TemporalPhase.MANIFESTING
        stability = 1.0

        effort = 0.3
        uncertainty = 0.1

        category = ContractIntentCategory.CHIT_CHAT
        purity = 1.0

        text_response = "I hear you."

        reflective_signal = any(
            w in text for w in [
                "feel", "sad", "void", "meaning", "grief", "lonely", "heart", "soul", "true"
            ]
        )

        # Legacy-compatible defaults used by older consumers and tests.
        legacy_intent_category = IntentCategory.CHAT
        semantic_concepts = []
        base_shape = BaseShape.SPHERE
        color_palette = "#FFFFFF"

        # 1. Detect Category
        if any(w in text for w in ["search", "find", "analyze", "check", "what", "how", "solve"]):
            category = ContractIntentCategory.ANALYTIC
            effort = 0.8
            text_response = "Analyzing data structure alignment."
            legacy_intent_category = IntentCategory.REQUEST
            semantic_concepts.append("inquiry")
            base_shape = BaseShape.CUBE
            color_palette = "#00FFFF"
        elif any(w in text for w in ["stop", "start", "reset", "clear", "system", "status", "make"]):
            category = ContractIntentCategory.SYSTEM_OPS
            effort = 0.2
            text_response = "System operations engaged."
            legacy_intent_category = IntentCategory.COMMAND
            semantic_concepts.append("directive")
            base_shape = BaseShape.CUBE
            color_palette = "#00FF00"
        elif any(w in text for w in ["story", "imagine", "create", "poem", "idea"]):
            category = ContractIntentCategory.CREATIVE
            effort = 0.6
            uncertainty = 0.3 # Creative chaos
            text_response = "Imagining a new possibility."
            legacy_intent_category = IntentCategory.CHAT
            semantic_concepts.append("creative")
            base_shape = BaseShape.CLOUD
            color_palette = "#FF00FF"

        if reflective_signal:
            # Deep reflective inputs should remain calm, high-effort, and semantically rich.
            category = ContractIntentCategory.CREATIVE
            effort = max(effort, 0.95)
            uncertainty = min(uncertainty, 0.2)
            text_response = "I sense deep context and signal density in this reflection."
            if "reflective" not in semantic_concepts:
                semantic_concepts.append("reflective")
            color_palette = "#800080"

        if any(w in text for w in ["error", "failure", "critical"]):
            legacy_intent_category = IntentCategory.ERROR
            base_shape = BaseShape.CRACKS
            color_palette = "#FF4500"
            semantic_concepts.append("instability")

        if any(w in text for w in ["deep", "wisdom", "spiral"]):
            base_shape = BaseShape.VORTEX
            color_palette = "#800080"

        # 2. Detect Nuance
        if "hard" in text or "complex" in text:
            effort = 1.0
        if "maybe" in text or "unsure" in text:
            uncertainty = 0.8

        return EmbodimentContract(
            temporal_state=TemporalState(phase=phase, stability=stability, duration_ms=0),
            cognitive=CognitiveMetadata(effort=effort, uncertainty=uncertainty),
            intent=IntentData(category=category, purity=purity),
            text_content=text_response,
            intent_category=legacy_intent_category,
            semantic_concepts=semantic_concepts,
            visual_parameters=VisualSpecifics(
                base_shape=base_shape,
                turbulence=min(1.0, uncertainty),
                particle_density=max(0.1, min(1.0, 0.4 + (effort * 0.4))),
                color_palette=color_palette,
                flow_direction="none",
            ),
        )
