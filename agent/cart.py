"""Plan reversible edits through current, visible Storefront controls."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING
from uuid import uuid4

from agent.schemas import Action, AskShopperAction, ClickAction, SelectAction, Snapshot, TypeAction

if TYPE_CHECKING:
    from agent.llm.intent import StructuredIntent

MESSAGES = {
    "add": ("تمت الإضافة إلى السلة", "Added to cart"),
    "quantity": ("تم تحديث الكمية", "Quantity updated"),
    "remove": ("تم حذف المنتج من السلة", "Item removed from cart"),
    "undo": ("تم التراجع عن تعديل السلة", "Cart change undone"),
}


def validate_cart_intent(message: str, intent: StructuredIntent) -> None:
    if not intent.cart_source or intent.cart_source.casefold() not in message.casefold():
        raise ValueError("Cart edits require current Shopper source")
    if re.search(r"\b(?:not|never|don't|without)\b|(?:^|\s)(?:لا|مش|ما)(?=\s|\w)", message, re.I):
        raise ValueError("Negated cart edit")
    cues = {
        "add": r"\badd\b|ضيف|أضف|اضف|حط",
        "quantity": r"quantity|change|set|كمية|خلي|غير",
        "remove": r"remove|delete|شيل|احذف|حذف",
        "undo": r"undo|تراجع|رجع",
    }
    if not re.search(cues[intent.cart_operation], intent.cart_source, re.I):
        raise ValueError("Cart operation needs an explicit request")
    if intent.cart_target and intent.cart_target.casefold() not in message.casefold():
        raise ValueError("Cart target must be sourced from the Shopper")
    for value in (intent.constraints.size, intent.constraints.color):
        normalized = message.translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
        if value and not re.search(rf"(?<!\w){re.escape(value)}(?!\w)", normalized, re.I):
            raise ValueError("Cart variant must be explicitly requested")
    if intent.cart_quantity is not None:
        digits = message.translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
        if not re.search(rf"(?<!\d){intent.cart_quantity}(?!\d)", digits):
            raise ValueError("Cart quantity must be explicitly requested")


def plan_cart_edit(
    intent: StructuredIntent, snapshot: Snapshot, task_id: str, sequence: int
) -> list[Action]:
    elements = [e for e in snapshot.elements if e.visible and not e.sensitive and not e.disabled]
    route = {
        "add": "/cart/items",
        "quantity": "/cart/quantity",
        "remove": "/cart/remove",
        "undo": "/cart/undo",
    }[intent.cart_operation]
    buttons = [e for e in elements if e.role == "button" and e.form_action == route]
    if intent.cart_target:
        buttons = [e for e in buttons if intent.cart_target.casefold() in e.name.casefold()]
    actions: list[Action] = []

    def base():
        return dict(
            v=1,
            task_id=task_id,
            action_id=f"action-{uuid4().hex}",
            sequence_number=sequence + len(actions),
            narration="هعدّل السلة مع إمكانية التراجع."
            if intent.language == "ar"
            else "I'll update the cart with an Undo option.",
        )

    def handback():
        text = (
            "اختار المنتج والمقاس واللون من الصفحة، ثم اطلب التعديل مرة تانية."
            if intent.language == "ar"
            else "Choose the item, size and colour on the page, then request the change again."
        )
        return [
            AskShopperAction(
                **{**base(), "sequence_number": sequence},
                type="ask_shopper",
                question=text,
                options=["Stop"],
            )
        ]

    if len(buttons) != 1 or intent.needs_clarification:
        return handback()
    if intent.cart_operation == "add":
        for name, desired in [
            ("المقاس", intent.constraints.size),
            ("اللون", intent.constraints.color),
        ]:
            controls = [e for e in elements if e.role == "combobox" and e.name == name]
            if len(controls) != 1 or not (desired or controls[0].value):
                return handback()
            control = controls[0]
            if desired and desired != control.value:
                if desired not in (control.options or []):
                    return handback()
                actions.append(SelectAction(**base(), type="select", id=control.id, option=desired))
    if intent.cart_operation in {"add", "quantity"} and intent.cart_quantity is not None:
        name = (
            "الكمية"
            if intent.cart_operation == "add"
            else buttons[0].name.replace("تحديث الكمية", "الكمية", 1)
        )
        controls = [e for e in elements if e.name == name and e.role == "textbox"]
        if len(controls) != 1:
            return handback()
        actions.append(
            TypeAction(
                **base(),
                type="type",
                id=controls[0].id,
                text=str(intent.cart_quantity),
                submit=False,
            )
        )
    elif intent.cart_operation == "quantity":
        return handback()
    actions.append(ClickAction(**base(), type="click", id=buttons[0].id))
    return actions


def scripted_cart_intent(message: str) -> StructuredIntent | None:
    from agent.llm.intent import StructuredIntent

    patterns = [
        ("add", r"(?:add (?:this|it) to (?:my |the )?cart|ضيف ده للسلة|أضف إلى السلة)"),
        ("remove", r"(?:remove (?:this|the) item|شيل المنتج ده)"),
        ("undo", r"(?:undo|تراجع)"),
        ("quantity", r"(?:set quantity to|خلي الكمية) (\d+)"),
    ]
    for kind, pattern in patterns:
        match = re.fullmatch(pattern, message.strip(), re.I)
        if match:
            ar = bool(re.search(r"[\u0600-\u06ff]", message))
            return StructuredIntent.model_validate(
                dict(
                    v=5,
                    language="ar" if ar else "en",
                    dialect="egyptian_arabic" if ar else "english",
                    intent="cart_edit",
                    cart_operation=kind,
                    cart_source=message,
                    cart_quantity=int(match[1]) if kind == "quantity" else None,
                    constraints={},
                    missing_fields=[],
                    needs_clarification=False,
                )
            )
    return None
