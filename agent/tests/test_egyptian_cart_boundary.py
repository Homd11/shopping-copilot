import asyncio
import json

import pytest

from agent.llm import interpret_message
from agent.llm.contract import LLMChunk, ScriptedLLMClient
from agent.storefront import load_storefront_definition


def interpret(message, fields):
    payload = {
        "v": 6,
        "language": "ar",
        "dialect": "egyptian_arabic",
        "constraints": {},
        "missing_fields": [],
        "needs_clarification": False,
        **fields,
    }
    return asyncio.run(
        interpret_message(
            ScriptedLLMClient([[LLMChunk(text=json.dumps(payload))]]),
            message,
            storefront=load_storefront_definition(),
            resolved_state={},
            pending_clarification=None,
        )
    )


def test_owner_bulk_clear_wording_reaches_guarded_intent_boundary():
    message = "شيل الحاجة اللي فالسلة كلها"
    result = interpret(
        message, {"intent": "mutate", "mutation_kind": "clear_cart", "mutation_source": message}
    )
    assert result.mutation_kind == "clear_cart"


@pytest.mark.parametrize("message", ["شيل صانع اللعب من السلة", "ما تشيل الحاجة اللي فالسلة كلها"])
def test_single_removal_and_negation_cannot_authorize_bulk_clear(message):
    with pytest.raises(ValueError):
        interpret(
            message, {"intent": "mutate", "mutation_kind": "clear_cart", "mutation_source": message}
        )


@pytest.mark.parametrize("quantity,accepted", [(1, True), (2, False)])
def test_attached_arabic_preposition_preserves_exact_quantity_evidence(quantity, accepted):
    message = "قلل كمية صانع اللعب بواحد"
    fields = {
        "intent": "cart_edit",
        "cart_operation": "quantity",
        "cart_source": message,
        "cart_target": "صانع اللعب",
        "cart_quantity": quantity,
        "cart_quantity_mode": "decrease",
    }
    if accepted:
        assert interpret(message, fields).cart_quantity == 1
    else:
        with pytest.raises(ValueError):
            interpret(message, fields)
