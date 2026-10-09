"""Operation-specific generation contracts; execution still validates StructuredIntent.

Derive field types from the persisted model to avoid a second set of money, variant,
and language definitions. The wire union prevents discovery metadata from leaking
into cart/navigation decisions instead of paying for a repair after generation.
"""

from copy import deepcopy
from functools import reduce
from operator import or_
from typing import Literal

from pydantic import TypeAdapter, create_model

from agent.llm.intent import IntentConstraints, IntentModel, StructuredIntent


def _fields(model, names):
    return {
        name: (model.model_fields[name].annotation, deepcopy(model.model_fields[name]))
        for name in names
    }


def _constraints(name, fields):
    return create_model(name, __base__=IntentModel, **_fields(IntentConstraints, fields))


_common = ("language", "dialect", "missing_fields", "conflicting_fields", "needs_clarification")


def _branch(name, intents, fields, constraints):
    return create_model(
        name,
        __base__=IntentModel,
        v=(Literal[9], ...),
        intent=(Literal[tuple(intents)], ...),
        constraints=(constraints, ...),
        **_fields(StructuredIntent, (*_common, *fields)),
    )


_branches = (
    _branch(
        "DiscoveryDecision",
        ("advice", "find_products"),
        (
            "catalogue_requirements",
            "price_preference",
            "owned_item",
            "desired_wear_position",
            "request_mode",
            "owned_items",
            "preferred_colors",
            "subjective_preferences",
            "advice_product_ids",
            "revised_fields",
            "revision_source",
        ),
        _constraints(
            "DiscoveryConstraints",
            tuple(n for n in IntentConstraints.model_fields if n != "target"),
        ),
    ),
    _branch(
        "CartDecision",
        ("cart_edit",),
        (
            "product_id",
            "cart_operation",
            "cart_source",
            "cart_target_id",
            "cart_quantity",
            "cart_quantity_mode",
        ),
        _constraints("CartVariants", ("size", "color")),
    ),
    _branch(
        "NavigationDecision",
        ("navigate", "locate"),
        ("navigation_source",),
        _constraints("Destination", ("target",)),
    ),
    _branch(
        "ProductDecision",
        ("open_product",),
        ("product_id", "navigation_source"),
        _constraints("ProductNavigationConstraints", ()),
    ),
    _branch(
        "MutationDecision",
        ("mutate",),
        ("mutation_kind", "mutation_source"),
        _constraints("MutationConstraints", ()),
    ),
    _branch(
        "ConversationDecision",
        ("help", "off_topic", "unsupported"),
        (),
        _constraints("ConversationConstraints", ()),
    ),
)

wire_intent_adapter = TypeAdapter(reduce(or_, _branches))
