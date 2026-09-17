import re
from dataclasses import dataclass
from typing import Literal
from urllib.parse import parse_qs, urlsplit

from agent.discovery import DiscoveryConstraints, build_discovery_url
from agent.schemas import (
    Action,
    AskShopperAction,
    ClickAction,
    NavigateAction,
    SelectAction,
    Snapshot,
    SnapshotElement,
    TypeAction,
)
from agent.storefront import StorefrontDefinition, load_storefront_definition, normalize_money

_ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
_LATIN_DIGITS = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
_NUMBER = r"[0-9٠-٩۰-۹][0-9٠-٩۰-۹.,٬٫]*"
Language = Literal["ar", "en"]


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


def _minimum_price_text(message: str) -> str | None:
    minimum = re.search(
        rf"(?:at\s+least|over|above|more\s+than|أكتر\s+من|اكتر\s+من|أكثر\s+من|اكثر\s+من)\s*({_NUMBER})",
        message,
        re.IGNORECASE,
    )
    return minimum.group(1) if minimum else None


def _budget_text(message: str, *, allow_currency_fallback: bool = True) -> str | None:
    budget = re.search(
        rf"(?:under|below|less\s+than|ta7t|تحت|أقل\s+من|اقل\s+من|حد\s+أقصى)\s*({_NUMBER})",
        message,
        re.IGNORECASE,
    )
    if budget:
        return budget.group(1)
    if not allow_currency_fallback:
        return None
    currency_amount = re.search(
        rf"({_NUMBER})\s*(?:egp|جنيه(?:\s+مصري)?|ج\s*\.\s*م)", message, re.IGNORECASE
    )
    return currency_amount.group(1) if currency_amount else None


def _unquoted_query(message: str, category_vocabulary: dict[str, tuple[str, ...]]) -> str | None:
    category_terms = sorted(
        (term for terms in category_vocabulary.values() for term in terms),
        key=len,
        reverse=True,
    )
    category_pattern = "|".join(re.escape(term) for term in category_terms)
    query_first = re.search(
        rf"(?:find|search(?:\s+for)?)\s+(.+?)\s+(?:in\s+)?(?:{category_pattern})(?:\s|$)",
        message,
        re.IGNORECASE,
    )
    if query_first:
        return query_first.group(1).strip()
    category_first = re.search(
        rf"(?:find|search)\s+(?:{category_pattern})\s+for\s+(.+)$",
        message,
        re.IGNORECASE,
    )
    return category_first.group(1).strip() if category_first else None


def _element_named(
    snapshot: Snapshot,
    terms: tuple[str, ...],
    *,
    roles: tuple[str, ...] | None = None,
) -> SnapshotElement | None:
    return next(
        (
            element
            for element in snapshot.elements
            if element.visible
            and (roles is None or element.role in roles)
            and any(term in element.name.lower() for term in terms)
        ),
        None,
    )


def snapshot_matches_url(snapshot: Snapshot, expected_url: str) -> bool:
    expected = urlsplit(expected_url)
    actual = urlsplit(snapshot.url)
    return actual.path == expected.path and parse_qs(actual.query) == parse_qs(expected.query)


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

        vocabulary = self._storefront.vocabulary
        category = _first_match(normalized, vocabulary.categories)
        if category is None:
            return self._ask_for_category(is_arabic=is_arabic, identity=identity)

        product_type = _first_match(normalized, vocabulary.types)
        color = _first_match(normalized, vocabulary.colors)
        query_match = re.search(r'["“]([^"”]+)["”]', message)
        size_match = re.search(r"(?:size|مقاس)\s*([0-9a-z]+)", normalized, re.IGNORECASE)
        minimum_text = _minimum_price_text(normalized)
        budget_text = _budget_text(normalized, allow_currency_fallback=minimum_text is None)
        minimum = (
            normalize_money(minimum_text, currency=self._storefront.currency)
            if minimum_text is not None
            else None
        )
        maximum = (
            normalize_money(budget_text, currency=self._storefront.currency)
            if budget_text is not None
            else None
        )
        if any(term in normalized for term in vocabulary.availability["unavailable"]):
            availability = False
        elif any(term in normalized for term in vocabulary.availability["available"]):
            availability = True
        else:
            availability = None
        sort = None
        if any(term in normalized for term in vocabulary.sort["cheapest"]):
            sort = "cheapest"
        elif any(term in normalized for term in vocabulary.sort["newest"]):
            sort = "newest"

        constraints = DiscoveryConstraints(
            category=category,
            query=(
                query_match.group(1)
                if query_match
                else _unquoted_query(message, vocabulary.categories)
            ),
            product_type=product_type,
            min_price=minimum,
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
        category = (
            _first_match(original_normalized, self._storefront.vocabulary.categories) or "shoes"
        )
        category_name = self._storefront.categories[category]
        product_type = _first_match(original_normalized, self._storefront.vocabulary.types)
        task = f"{category_name.en} under {amount} EGP"
        if product_type:
            task = f"{product_type} {task}"
        return self.plan(task, snapshot, identity)

    def plan_visible_control_fallback(
        self,
        expected_url: str,
        snapshot: Snapshot,
        identity: ActionIdentity,
        language: Language,
    ) -> Action:
        expected = urlsplit(expected_url)
        actual = urlsplit(snapshot.url)
        target = parse_qs(expected.query)
        current = parse_qs(actual.query)
        narration = (
            "هستخدم الفلاتر الظاهرة عشان أكمل الطلب."
            if language == "ar"
            else "I'll use the visible filters to finish the request."
        )
        staged_control = False
        for name, values in target.items():
            if current.get(name) == values:
                continue
            value = values[0]
            if name == "type":
                type_terms = self._storefront.vocabulary.types.get(value, (value,))
                element = _element_named(snapshot, type_terms, roles=("radio",))
                if element is not None and element.checked:
                    staged_control = True
                    continue
                if element is not None:
                    return ClickAction(
                        v=1,
                        type="click",
                        task_id=identity.task_id,
                        action_id=identity.action_id,
                        sequence_number=identity.sequence_number,
                        narration=narration,
                        id=element.id,
                    )
            elif name in ("availability", "sort"):
                element = _element_named(
                    snapshot,
                    self._storefront.vocabulary.controls[name],
                    roles=("combobox",),
                )
                if element is not None and element.value == value:
                    staged_control = True
                    continue
                if element is not None:
                    return SelectAction(
                        v=1,
                        type="select",
                        task_id=identity.task_id,
                        action_id=identity.action_id,
                        sequence_number=identity.sequence_number,
                        narration=narration,
                        id=element.id,
                        option=value,
                    )
            else:
                terms = self._storefront.vocabulary.controls.get(name)
                element = (
                    _element_named(snapshot, terms, roles=("textbox", "searchbox"))
                    if terms is not None
                    else None
                )
                if element is not None and element.value == value:
                    staged_control = True
                    continue
                if element is not None:
                    return TypeAction(
                        v=1,
                        type="type",
                        task_id=identity.task_id,
                        action_id=identity.action_id,
                        sequence_number=identity.sequence_number,
                        narration=narration,
                        id=element.id,
                        text=value,
                        submit=True,
                    )

        if staged_control:
            submit = _element_named(
                snapshot,
                self._storefront.vocabulary.controls["submit"],
                roles=("button",),
            )
            if submit is not None:
                return ClickAction(
                    v=1,
                    type="click",
                    task_id=identity.task_id,
                    action_id=identity.action_id,
                    sequence_number=identity.sequence_number,
                    narration=narration,
                    id=submit.id,
                )

        return AskShopperAction(
            v=1,
            type="ask_shopper",
            task_id=identity.task_id,
            action_id=identity.action_id,
            sequence_number=identity.sequence_number,
            narration=narration,
            question=(
                "الفلاتر المتوقعة مش ظاهرة. تحب نوقف ولا تحاول بنفسك؟"
                if language == "ar"
                else (
                    "The expected filters are not visible. "
                    "Would you like to stop or continue manually?"
                )
            ),
            options=["إيقاف", "هكمل بنفسي"] if language == "ar" else ["Stop", "Continue manually"],
        )
