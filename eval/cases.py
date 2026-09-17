from dataclasses import dataclass
from typing import Literal

AssertionKind = Literal[
    "url_matches",
    "element_visible",
    "element_spotlighted",
    "store_state",
    "panel_text",
]
Language = Literal["ar", "en"]
ExpectedStatus = Literal["complete", "question"]


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
    expected_status: ExpectedStatus = "complete"


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

DISCOVERY_CASES = INITIAL_FILTER_CASES + (
    EvaluationCase(
        case_id="filter-franco",
        message="3ayez kootshi running ta7t 2,000 EGP",
        language="en",
        assertions=FILTER_ASSERTIONS,
    ),
    EvaluationCase(
        case_id="filter-mixed",
        message="عاوز black running shoes مقاس 42 تحت 2500 EGP والأرخص",
        language="ar",
        assertions=(
            EvaluationAssertion(
                kind="url_matches",
                target=(
                    r"/c/shoes\?type=running&max_price=2500&size=42&color=black&sort=cheapest$"
                ),
            ),
            EvaluationAssertion(
                kind="element_visible", target="#results-heading", expected="2 منتجات"
            ),
            EvaluationAssertion(kind="store_state", target="filters.size", expected="42"),
            EvaluationAssertion(kind="store_state", target="filters.color", expected="black"),
            EvaluationAssertion(kind="store_state", target="filters.sort", expected="cheapest"),
            EvaluationAssertion(kind="store_state", target="product_count", expected="2"),
        ),
    ),
    EvaluationCase(
        case_id="filter-unavailable",
        message="Show unavailable bags newest first",
        language="en",
        assertions=(
            EvaluationAssertion(
                kind="url_matches",
                target=r"/c/bags\?availability=unavailable&sort=newest$",
            ),
            EvaluationAssertion(
                kind="element_visible", target="#results-heading", expected="3 منتجات"
            ),
            EvaluationAssertion(
                kind="store_state", target="filters.availability", expected="unavailable"
            ),
            EvaluationAssertion(kind="store_state", target="filters.sort", expected="newest"),
            EvaluationAssertion(kind="store_state", target="product_count", expected="3"),
        ),
    ),
    EvaluationCase(
        case_id="filter-empty",
        message="Show black running shoes size 99 under 100 EGP",
        language="en",
        assertions=(
            EvaluationAssertion(
                kind="element_visible", target="#results-heading", expected="0 منتجات"
            ),
            EvaluationAssertion(
                kind="element_visible",
                target='[role="status"]',
                expected="لا توجد منتجات مطابقة. جرّب إزالة فلتر اللون.",
            ),
            EvaluationAssertion(kind="store_state", target="product_count", expected="0"),
        ),
    ),
    EvaluationCase(
        case_id="ask-ambiguous",
        message="Show me something under 1000 EGP",
        language="en",
        assertions=(
            EvaluationAssertion(
                kind="panel_text",
                target="#pending-question p",
                expected="Which category should I search?",
            ),
        ),
        expected_status="question",
    ),
)
