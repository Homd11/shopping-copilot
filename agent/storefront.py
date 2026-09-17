from __future__ import annotations

import json
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

SUPPORTED_FILTERS = (
    "q",
    "type",
    "min_price",
    "max_price",
    "size",
    "color",
    "availability",
    "sort",
)


class StorefrontDefinitionError(ValueError):
    """The authoritative Storefront Definition cannot be used safely."""


class UnsupportedCurrencyError(ValueError):
    """A Shopper supplied a currency the EGP-only Storefront does not support."""


@dataclass(frozen=True)
class CategoryDefinition:
    ar: str
    en: str


@dataclass(frozen=True)
class StorefrontDefinition:
    v: int
    name: str
    currency: str
    category_route: str
    filters: tuple[str, ...]
    categories: dict[str, CategoryDefinition]


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal):
            raise TypeError("Money amount must be a Decimal")
        if not self.amount.is_finite() or self.amount < 0:
            raise ValueError("Money amount must be a non-negative finite decimal")
        if not isinstance(self.currency, str) or not re.fullmatch(r"[A-Z]{3}", self.currency):
            raise ValueError("Money currency must be an uppercase ISO currency code")


def _definition_path() -> Path:
    return Path(__file__).resolve().parents[1] / "storefront-definition.json"


def _required_mapping(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise StorefrontDefinitionError(f"{key} must be an object")
    return value


def load_storefront_definition(
    path: str | Path | None = None,
) -> StorefrontDefinition:
    definition_path = Path(path) if path is not None else _definition_path()
    try:
        payload = json.loads(definition_path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise StorefrontDefinitionError(
            f"Storefront Definition not found: {definition_path}"
        ) from error
    except json.JSONDecodeError as error:
        raise StorefrontDefinitionError(
            f"Storefront Definition is not valid JSON: {error.msg}"
        ) from error

    return parse_storefront_definition(payload)


def parse_storefront_definition(payload: object) -> StorefrontDefinition:
    """Validate decoded Storefront Definition data without guessing defaults."""

    if not isinstance(payload, dict):
        raise StorefrontDefinitionError("Storefront Definition must be an object")
    if payload.get("v") != 1:
        raise StorefrontDefinitionError("v must be 1")
    name = payload.get("name")
    if not isinstance(name, str) or not name.strip():
        raise StorefrontDefinitionError("name must be a non-empty string")
    if "currency" not in payload:
        raise StorefrontDefinitionError("currency is required")
    currency = payload["currency"]
    if not isinstance(currency, str):
        raise StorefrontDefinitionError("currency must be a string")
    if currency != "EGP":
        raise StorefrontDefinitionError("currency must be EGP for the local MVP")

    routes = _required_mapping(payload, "routes")
    category_route = routes.get("category")
    if not isinstance(category_route, str) or category_route.count("{category}") != 1:
        raise StorefrontDefinitionError("routes.category must contain one {category} placeholder")

    raw_filters = payload.get("filters")
    if not isinstance(raw_filters, list) or not all(isinstance(item, str) for item in raw_filters):
        raise StorefrontDefinitionError("filters must be a list of strings")
    unknown_filters = [item for item in raw_filters if item not in SUPPORTED_FILTERS]
    if unknown_filters:
        raise StorefrontDefinitionError(
            f"unsupported filter in Storefront Definition: {unknown_filters[0]}"
        )
    if len(set(raw_filters)) != len(raw_filters):
        raise StorefrontDefinitionError("filters must not contain duplicates")

    raw_categories = _required_mapping(payload, "categories")
    if not raw_categories:
        raise StorefrontDefinitionError("categories must not be empty")
    categories: dict[str, CategoryDefinition] = {}
    for slug, raw_category in raw_categories.items():
        if not isinstance(slug, str) or not re.fullmatch(r"[a-z][a-z0-9-]*", slug):
            raise StorefrontDefinitionError("category slugs must be URL-safe strings")
        if not isinstance(raw_category, dict):
            raise StorefrontDefinitionError(f"category {slug} must be an object")
        ar = raw_category.get("ar")
        en = raw_category.get("en")
        if not isinstance(ar, str) or not ar.strip() or not isinstance(en, str) or not en.strip():
            raise StorefrontDefinitionError(f"category {slug} must have non-empty ar and en names")
        categories[slug] = CategoryDefinition(ar=ar, en=en)

    return StorefrontDefinition(
        v=1,
        name=name,
        currency=currency,
        category_route=category_route,
        filters=tuple(raw_filters),
        categories=categories,
    )


_DIGIT_TRANSLATION = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
_EGP_MARKERS = re.compile(
    r"(?:\bEGP\b|\bL\.?\s*E\.?\b|ج\s*\.\s*م|جنيه(?:\s+مصري)?)",
    re.IGNORECASE,
)
_OTHER_CURRENCIES = re.compile(
    r"(?:\$|€|£|\bUSD\b|\bEUR\b|\bGBP\b|\bSAR\b|ر\s*\.\s*س|ريال(?:\s+سعودي)?)",
    re.IGNORECASE,
)


def _normalize_decimal_text(text: str) -> str:
    compact = re.sub(r"\s+", "", text)
    if not compact or not re.fullmatch(r"[0-9.,]+", compact):
        raise ValueError("money amount is malformed")

    if "," in compact and "." in compact:
        decimal_separator = "," if compact.rfind(",") > compact.rfind(".") else "."
        thousands_separator = "." if decimal_separator == "," else ","
        whole, fraction = compact.rsplit(decimal_separator, 1)
        groups = whole.split(thousands_separator)
        if (
            not (1 <= len(fraction) <= 2)
            or not fraction.isdigit()
            or len(groups) < 2
            or not groups[0].isdigit()
            or not all(len(group) == 3 and group.isdigit() for group in groups[1:])
        ):
            raise ValueError("money amount has malformed separators")
        return f"{''.join(groups)}.{fraction}"

    if "," in compact:
        groups = compact.split(",")
        if (
            len(groups) == 2
            and 1 <= len(groups[1]) <= 2
            and all(group.isdigit() for group in groups)
        ):
            return f"{groups[0]}.{groups[1]}"
        if groups[0].isdigit() and all(len(group) == 3 and group.isdigit() for group in groups[1:]):
            return "".join(groups)
        raise ValueError("money amount has malformed separators")

    if compact.count(".") > 1:
        groups = compact.split(".")
        if groups[0].isdigit() and all(len(group) == 3 and group.isdigit() for group in groups[1:]):
            return "".join(groups)
        raise ValueError("money amount has malformed separators")
    if "." in compact:
        whole, fraction = compact.split(".")
        if whole.isdigit() and len(fraction) == 3 and fraction.isdigit():
            return f"{whole}{fraction}"
        if not whole.isdigit() or not fraction.isdigit() or not (1 <= len(fraction) <= 2):
            raise ValueError("money amount has malformed separators")
    return compact


def normalize_money(text: str, *, currency: str) -> Money:
    if currency != "EGP":
        raise StorefrontDefinitionError("configured currency must be EGP")
    if not isinstance(text, str):
        raise TypeError("money text must be a string")
    normalized = text.translate(_DIGIT_TRANSLATION).replace("٬", ",").replace("٫", ".")
    if _OTHER_CURRENCIES.search(normalized):
        raise UnsupportedCurrencyError("Currency conversion is unavailable; provide an EGP amount")
    normalized = _EGP_MARKERS.sub("", normalized).strip()
    if normalized.startswith("-"):
        raise ValueError("money amount must not be negative")
    decimal_text = _normalize_decimal_text(normalized)
    try:
        amount = Decimal(decimal_text)
    except InvalidOperation as error:
        raise ValueError("money amount is malformed") from error
    return Money(amount=amount, currency=currency)
