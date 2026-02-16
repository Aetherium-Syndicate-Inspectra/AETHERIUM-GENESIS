import pytest
import asyncio
from src.backend.genesis_core.logenesis.simulated_interpreter import SimulatedIntentInterpreter
from src.backend.genesis_core.models.visual import ContractIntentCategory

@pytest.mark.asyncio
async def test_simulated_interpreter_logic():
    interpreter = SimulatedIntentInterpreter()

    # Case 1: Search Request -> ANALYTIC
    res1 = await interpreter.interpret("search for quantum physics")
    assert res1.intent.category == ContractIntentCategory.ANALYTIC
    assert res1.text_content == "Analyzing data structure."

    # Case 2: Command / Structure -> ANALYTIC (matches 'solve', 'check', etc)
    # Wait, 'cube' doesn't match keywords in SimulatedIntentInterpreter.
    # Let's use 'status' for SYSTEM_OPS
    res2 = await interpreter.interpret("system status")
    assert res2.intent.category == ContractIntentCategory.SYSTEM_OPS
    assert res2.text_content == "System operations engaged."

    # Case 3: Poem -> CREATIVE
    res3 = await interpreter.interpret("write a poem")
    assert res3.intent.category == ContractIntentCategory.CREATIVE
    assert res3.text_content == "Imagining a new possibility."

    # Case 4: Deep Thought / Reflection
    res4 = await interpreter.interpret("what is the meaning of life")
    # 'what' -> ANALYTIC, but 'meaning' -> Reflective (CREATIVE override)
    assert res4.intent.category == ContractIntentCategory.CREATIVE
    assert "deep context" in res4.text_content
