from playwright.sync_api import sync_playwright

from eval.cases import DISCOVERY_CASES, EvaluationAssertion, EvaluationCase
from eval.runner import run_evaluation
from eval.services import local_services


def test_bilingual_discovery_cases_run_through_the_real_browser_path() -> None:
    with local_services(), sync_playwright() as playwright:
        results = run_evaluation(playwright.chromium, DISCOVERY_CASES)

    assert [result.case_id for result in results] == [
        "filter-ar",
        "filter-en",
        "filter-franco",
        "filter-mixed",
        "filter-unavailable",
        "filter-empty",
        "ask-ambiguous",
    ]
    assert all(result.passed for result in results), [result.failure for result in results]
    assert [result.step_count for result in results] == [1, 1, 1, 1, 1, 1, 0]
    assert all(result.elapsed_ms > 0 for result in results)
    assert all(result.failure is None for result in results)


def test_case_timeout_is_reported_within_the_case_deadline() -> None:
    timeout_case = EvaluationCase(
        case_id="bounded-timeout",
        message="Show me running shoes under 2000 EGP",
        language="en",
        timeout_ms=750,
        assertions=(EvaluationAssertion(kind="element_visible", target="#never-appears"),),
    )

    with local_services(), sync_playwright() as playwright:
        result = run_evaluation(playwright.chromium, (timeout_case,))[0]

    assert result.passed is False
    assert "Timeout" in (result.failure or "")
    assert result.elapsed_ms < 2_000
