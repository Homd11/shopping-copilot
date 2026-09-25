"""Plan reversible edits through current, visible Storefront controls."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING
from uuid import uuid4

from agent.schemas import Action, AskShopperAction, ClickAction, SelectAction, Snapshot, TypeAction
from agent.storefront import load_storefront_definition

if TYPE_CHECKING:
    from agent.llm.intent import StructuredIntent

MESSAGES = {
    "add": ("تمت الإضافة إلى السلة", "Added to cart"),
    "quantity": ("تم تحديث الكمية", "Quantity updated"),
    "remove": ("تم حذف المنتج من السلة", "Item removed from cart"),
    "undo": ("تم التراجع عن تعديل السلة", "Cart change undone"),
}


def validate_cart_intent(message: str, intent: StructuredIntent) -> StructuredIntent:
    if not intent.cart_source or intent.cart_source.casefold() not in message.casefold():
        raise ValueError("Cart edits require current Shopper source")
    if re.search(r"\b(?:not|never|don't|without)\b|(?:^|\s)(?:لا|مش|ما)(?=\s|\w)", message, re.I):
        raise ValueError("Negated cart edit")
    cues = {
        "add": r"\badd\b|ضيف|أضف|اضف|حط",
        "quantity": (
            r"quantity|change|set|increase|decrease|reduce|add|ضيف|كمية"
            r"|خلي|غير|زود|زوّد|قلل|نقص"
        ),
        "remove": r"remove|delete|شيل|احذف|حذف",
        "undo": r"undo|تراجع|رجع",
    }
    if not re.search(cues[intent.cart_operation], intent.cart_source, re.I):
        raise ValueError("Cart operation needs an explicit request")
    if intent.cart_target and intent.cart_target.casefold() not in message.casefold():
        raise ValueError("Cart target must be sourced from the Shopper")
    normalized = message.translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
    colors = load_storefront_definition().vocabulary.colors
    if intent.cart_operation == "add":
        requested_colors = [
            key
            for key, terms in colors.items()
            if any(
                re.search(
                    rf"(?:\bcolou?r\b|اللون|باللون|لونه)\s*(?:is\s+)?{re.escape(term)}(?!\w)",
                    normalized,
                    re.I,
                )
                for term in terms
            )
        ]
        size = re.search(r"(?:\bsize\b|مقاس(?:ي)?)\s*([\w-]+)", normalized, re.I)
        updates = {}
        if len(requested_colors) > 1:
            raise ValueError("Conflicting cart colors require clarification")
        if requested_colors:
            updates["color"] = requested_colors[0]
        if size:
            updates["size"] = size[1]
        for field, value in updates.items():
            if getattr(intent.constraints, field) not in {None, value}:
                raise ValueError("Cart variant contradicts the Shopper")
        intent = intent.model_copy(
            update={"constraints": intent.constraints.model_copy(update=updates)}
        )
    for field, value in [("size", intent.constraints.size), ("color", intent.constraints.color)]:
        terms = colors.get(value, (value,)) if field == "color" else (value,)
        if value and not any(
            re.search(rf"(?<!\w){re.escape(term)}(?!\w)", normalized, re.I) for term in terms
        ):
            raise ValueError("Cart variant must be explicitly requested")
    if intent.cart_operation == "quantity":
        mode = intent.cart_quantity_mode
        absolute = bool(re.search(r"\bto\s+\d|(?:إلى|الى)\s*\d", normalized, re.I))
        increase = bool(re.search(r"\bmore\b|كمان|\bincrease\b.*\bby\b|زود|زوّد", normalized, re.I))
        decrease = bool(
            re.search(r"\b(?:decrease|reduce)\b.*\bby\b|\bfewer\b|قلل|نقص", normalized, re.I)
        )
        expected = (
            "set" if absolute else "increase" if increase else "decrease" if decrease else None
        )
        if (intent.v == 6 and mode is None) or (expected and (mode or "set") != expected):
            raise ValueError("Relative quantity mode contradicts the Shopper")
    if intent.cart_quantity_mode in {"increase", "decrease"}:
        cue = (
            r"increase|add|more|زود|زوّد|كمان|زيادة"
            if intent.cart_quantity_mode == "increase"
            else r"decrease|reduce|less|fewer|قلل|نقص"
        )
        if not re.search(cue, intent.cart_source, re.I):
            raise ValueError("Relative quantity must be explicitly requested")
    if intent.cart_quantity is not None:
        digits = message.translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
        quantity_words = {
            1: ("one", "واحد", "واحدة"),
            2: ("two", "اتنين", "اثنين", "إتنين"),
            3: ("three", "تلاتة", "ثلاثة"),
            4: ("four", "اربعة", "أربعة"),
            5: ("five", "خمسة"),
        }
        explicit_word = any(
            re.search(
                rf"(?<!\w){'ب?' if re.search('[ء-ي]', word) else ''}{word}(?!\w)",
                message,
                re.I,
            )
            for word in quantity_words.get(intent.cart_quantity, ())
        )
        if not explicit_word and not re.search(rf"(?<!\d){intent.cart_quantity}(?!\d)", digits):
            raise ValueError("Cart quantity must be explicitly requested")

    return intent


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
        if intent.cart_operation == "add":
            headings = [e.name.casefold() for e in elements if e.role == "heading"]
            if not any(intent.cart_target.casefold() in name for name in headings):
                buttons = []
        else:
            buttons = [
                e
                for e in buttons
                if intent.cart_target.casefold() in f"{e.name} {e.group or ''}".casefold()
            ]
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

    for value in (intent.constraints.size, intent.constraints.color):
        if value and intent.cart_operation in {"quantity", "remove"}:
            buttons = [
                e
                for e in buttons
                if e.group and re.search(rf"(?<!\w){re.escape(value)}(?!\w)", e.group, re.I)
            ]
    unresolved = set(intent.missing_fields) - {"query", "product_id", "target", "size", "color"}
    if len(buttons) != 1 or intent.conflicting_fields or unresolved:
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
        controls = [
            e
            for e in elements
            if e.name == name
            and e.role == "textbox"
            and (not buttons[0].group or e.group == buttons[0].group)
        ]
        if len(controls) != 1:
            return handback()
        quantity = intent.cart_quantity
        if intent.cart_quantity_mode in {"increase", "decrease"}:
            try:
                current = int(controls[0].value or "")
            except ValueError:
                return handback()
            quantity = (
                current + quantity
                if intent.cart_quantity_mode == "increase"
                else current - quantity
            )
        if not 1 <= quantity <= 99:
            return handback()
        actions.append(
            TypeAction(
                **base(),
                type="type",
                id=controls[0].id,
                text=str(quantity),
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
    relative = re.fullmatch(r"Increase quantity by (\d+) for (.+)", message.strip(), re.I)
    if relative:
        return StructuredIntent.model_validate(
            dict(
                v=6,
                language="en",
                dialect="english",
                intent="cart_edit",
                cart_operation="quantity",
                cart_source=message,
                cart_target=relative[2],
                cart_quantity=int(relative[1]),
                cart_quantity_mode="increase",
                constraints={},
                missing_fields=[],
                needs_clarification=False,
            )
        )
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
