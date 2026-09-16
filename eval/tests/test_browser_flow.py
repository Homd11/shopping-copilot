from playwright.sync_api import sync_playwright

from eval.cases import INITIAL_FILTER_CASES, EvaluationAssertion, EvaluationCase
from eval.runner import run_evaluation
from eval.services import local_services


def test_arabic_and_english_filter_cases_run_through_the_real_browser_path() -> None:
    with local_services(), sync_playwright() as playwright:
        results = run_evaluation(playwright.chromium, INITIAL_FILTER_CASES)

    assert [result.case_id for result in results] == ["filter-ar", "filter-en"]
    assert all(result.passed for result in results), [result.failure for result in results]
    assert all(result.step_count == 1 for result in results)
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
