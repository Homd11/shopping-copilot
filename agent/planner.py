import re
from dataclasses import dataclass
from typing import Literal

from agent.discovery import DiscoveryConstraints, build_discovery_url
from agent.schemas import Action, AskShopperAction, NavigateAction, Snapshot
from agent.storefront import StorefrontDefinition, load_storefront_definition, normalize_money

_ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
_LATIN_DIGITS = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
_NUMBER = r"[0-9٠-٩۰-۹][0-9٠-٩۰-۹.,٬٫]*"
Language = Literal["ar", "en"]

_CATEGORY_TERMS = {
    "shoes": ("shoe", "shoes", "sneaker", "kootshi", "kotshi", "كوتشي", "حذاء", "أحذية"),
    "clothing": ("clothing", "clothes", "jacket", "ملابس", "هدوم", "جاكيت"),
    "bags": ("bag", "bags", "شنطة", "شنط"),
    "electronics": ("electronics", "phone", "mobile", "موبايل", "إلكترونيات"),
}
_TYPE_TERMS = {
    "running": ("running", "جري", "للجري", "gari", "gery"),
    "outerwear": ("jacket", "جاكيت"),
    "backpack": ("backpack", "حقيبة ظهر"),
    "headphones": ("headphones", "سماعات"),
}
_COLOR_TERMS = {
    "black": ("black", "اسود", "أسود"),
    "blue": ("blue", "ازرق", "أزرق"),
    "red": ("red", "احمر", "أحمر"),
    "white": ("white", "ابيض", "أبيض"),
}


def detect_language(message: str) -> Language:
    return "ar" if re.search(r"[\u0600-\u06ff]", message) else "en"


class UnsupportedShoppingTask(ValueError):
    pass


@dataclass(frozen=True)
class ActionIdentity:
    task_id: str
    action_id: str
    sequence_number: int


def _first_match(normalized: str, vocabulary: dict[str, tuple[str, ...]]) -> str | None:
    return next(
        (value for value, terms in vocabulary.items() if any(term in normalized for term in terms)),
        None,
    )


def _budget_text(message: str) -> str | None:
    budget = re.search(
        rf"(?:under|below|less\s+than|ta7t|تحت|أقل\s+من|اقل\s+من|حد\s+أقصى)\s*({_NUMBER})",
        message,
        re.IGNORECASE,
    )
    if budget:
        return budget.group(1)
    currency_amount = re.search(
        rf"({_NUMBER})\s*(?:egp|جنيه(?:\s+مصري)?|ج\s*\.\s*م)", message, re.IGNORECASE
    )
    return currency_amount.group(1) if currency_amount else None


class ScriptedPlanner:
    def __init__(self, storefront: StorefrontDefinition | None = None) -> None:
        self._storefront = storefront or load_storefront_definition()

    def _ask_for_category(self, *, is_arabic: bool, identity: ActionIdentity) -> AskShopperAction:
        categories = list(self._storefront.categories.values())
        return AskShopperAction(
            v=1,
            type="ask_shopper",
            task_id=identity.task_id,
            action_id=identity.action_id,
            sequence_number=identity.sequence_number,
            narration=(
                "محتاج أعرف القسم المناسب قبل ما أفلتر المنتجات."
                if is_arabic
                else "I need the product category before I can filter the catalogue."
            ),
            question="بتدور في قسم إيه؟" if is_arabic else "Which category should I search?",
            options=[category.ar if is_arabic else category.en for category in categories],
        )

    def plan(self, message: str, snapshot: Snapshot, identity: ActionIdentity) -> Action:
        del snapshot
        normalized = message.translate(_ARABIC_DIGITS).lower()
        is_arabic = detect_language(message) == "ar"
        if re.search(r"\b(?:usd|eur|gbp|sar|aed)\b|[$€£]", normalized):
            question = (
                "ميزانيتك كام بالجنيه المصري؟" if is_arabic else "What is your budget in EGP?"
            )
            narration = (
                "محتاج الميزانية بالجنيه المصري من غير تحويل عملة."
                if is_arabic
                else "I need an EGP budget and won't convert currencies."
            )
            return AskShopperAction(
                v=1,
                type="ask_shopper",
                task_id=identity.task_id,
                action_id=identity.action_id,
                sequence_number=identity.sequence_number,
                narration=narration,
                question=question,
                options=[],
            )

        category = _first_match(normalized, _CATEGORY_TERMS)
        if category is None:
            return self._ask_for_category(is_arabic=is_arabic, identity=identity)

        product_type = _first_match(normalized, _TYPE_TERMS)
        color = _first_match(normalized, _COLOR_TERMS)
        query_match = re.search(r'["“]([^"”]+)["”]', message)
        size_match = re.search(r"(?:size|مقاس)\s*([0-9a-z]+)", normalized, re.IGNORECASE)
        budget_text = _budget_text(normalized)
        maximum = (
            normalize_money(budget_text, currency=self._storefront.currency)
            if budget_text is not None
            else None
        )
        if any(term in normalized for term in ("unavailable", "out of stock", "غير متاح", "خلصان")):
            availability = False
        elif any(term in normalized for term in ("available", "in stock", "متاح", "موجود")):
            availability = True
        else:
            availability = None
        sort = None
        if any(term in normalized for term in ("cheapest", "lowest price", "الأرخص")):
            sort = "cheapest"
        elif any(term in normalized for term in ("newest", "latest", "الأحدث")):
            sort = "newest"

        constraints = DiscoveryConstraints(
            category=category,
            query=query_match.group(1) if query_match else None,
            product_type=product_type,
            max_price=maximum,
            size=size_match.group(1) if size_match else None,
            color=color,
            availability=availability,
            sort=sort,
        )
        url = build_discovery_url(self._storefront, constraints)

        if category == "shoes" and product_type == "running" and maximum is not None:
            maximum_text = format(maximum.amount, "f")
            narration = (
                f"هفلتر لك أحذية الجري بحد أقصى {maximum_text.translate(_LATIN_DIGITS)} جنيه."
                if is_arabic
                else f"I'll filter running shoes to a maximum of EGP {maximum_text}."
            )
        else:
            category_name = self._storefront.categories[category]
            narration = (
                f"هعرض لك نتائج {category_name.ar} المطابقة."
                if is_arabic
                else f"I'll show matching {category_name.en.lower()}."
            )
        return NavigateAction(
            v=1,
            type="navigate",
            task_id=identity.task_id,
            action_id=identity.action_id,
            sequence_number=identity.sequence_number,
            narration=narration,
            url=url,
        )

    def plan_answer(
        self,
        original_message: str,
        answer: str,
        snapshot: Snapshot,
        identity: ActionIdentity,
    ) -> Action:
        category_by_answer = {
            category.en.lower(): slug for slug, category in self._storefront.categories.items()
        } | {category.ar: slug for slug, category in self._storefront.categories.items()}
        selected_category = category_by_answer.get(answer.strip().lower())
        if selected_category is not None:
            category_name = self._storefront.categories[selected_category]
            selected_name = (
                category_name.ar if detect_language(original_message) == "ar" else category_name.en
            )
            return self.plan(
                f"{original_message} {selected_name}",
                snapshot,
                identity,
            )

        amount_match = re.search(_NUMBER, answer)
        if amount_match is None or not re.search(r"\begp\b|جنيه|ج\s*\.\s*م", answer, re.IGNORECASE):
            raise UnsupportedShoppingTask("A budget answer must contain an EGP amount")
        amount = amount_match.group()
        original_normalized = original_message.lower()
        category = _first_match(original_normalized, _CATEGORY_TERMS) or "shoes"
        category_name = self._storefront.categories[category]
        product_type = _first_match(original_normalized, _TYPE_TERMS)
        task = f"{category_name.en} under {amount} EGP"
        if product_type:
            task = f"{product_type} {task}"
        return self.plan(task, snapshot, identity)
