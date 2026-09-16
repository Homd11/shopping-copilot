from dataclasses import dataclass
from typing import Literal

AssertionKind = Literal["url_matches", "element_visible", "element_spotlighted", "store_state"]
Language = Literal["ar", "en"]


@dataclass(frozen=True)
class EvaluationAssertion:
    kind: AssertionKind
    target: str
    expected: str | None = None


@dataclass(frozen=True)
class EvaluationCase:
    case_id: str
    message: str
    language: Language
    assertions: tuple[EvaluationAssertion, ...]
    timeout_ms: int = 10_000


FILTER_ASSERTIONS = (
    EvaluationAssertion(
        kind="url_matches",
        target=r"/c/shoes\?type=running&max_price=2000$",
    ),
    EvaluationAssertion(kind="element_visible", target="#results-heading", expected="3 منتجات"),
    EvaluationAssertion(
        kind="store_state",
        target="filters.type",
        expected="running",
    ),
    EvaluationAssertion(kind="store_state", target="filters.max_price", expected="2000"),
    EvaluationAssertion(kind="store_state", target="product_count", expected="3"),
)

INITIAL_FILTER_CASES = (
    EvaluationCase(
        case_id="filter-ar",
        message="عاوز كوتشي للجري بأقل من ٢٠٠٠",
        language="ar",
        assertions=FILTER_ASSERTIONS,
    ),
    EvaluationCase(
        case_id="filter-en",
        message="Show me running shoes under 2000 EGP",
        language="en",
        assertions=FILTER_ASSERTIONS,
    ),
)
