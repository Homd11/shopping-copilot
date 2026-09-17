import json
import re
import time
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit
from urllib.request import Request, urlopen

from playwright.sync_api import BrowserType, Frame, expect, sync_playwright

from eval.cases import DISCOVERY_CASES, EvaluationAssertion, EvaluationCase
from eval.services import local_services

PANEL_URL = "http://localhost:4100/"
RESET_URL = "http://localhost:4000/__test/reset"
STATE_URL = "http://localhost:4000/__test/state"


@dataclass(frozen=True)
class EvaluationResult:
    case_id: str
    passed: bool
    step_count: int
    elapsed_ms: float
    failure: str | None

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def remaining_timeout_ms(deadline: float) -> int:
    remaining = int((deadline - time.perf_counter()) * 1000)
    if remaining <= 0:
        raise TimeoutError("Evaluation Case exceeded its configured timeout")
    return remaining


def state_value(state: Mapping[str, Any], path: str) -> Any:
    value: Any = state
    for segment in path.split("."):
        if not isinstance(value, Mapping) or segment not in value:
            raise AssertionError(f"Authoritative Storefront state has no value at {path!r}")
        value = value[segment]
    return value


def _reset_storefront(timeout_ms: int) -> None:
    request = Request(RESET_URL, method="POST")
    with urlopen(  # noqa: S310 - fixed local evaluation URL
        request, timeout=max(timeout_ms / 1000, 0.001)
    ) as response:
        if response.status != 204:
            raise RuntimeError(f"Storefront reset failed with {response.status}")


def _frame_for_storefront(page) -> Frame:
    frame = page.frame(url=re.compile(r"http://localhost:4000/"))
    if frame is None:
        raise AssertionError("Storefront frame was not available")
    return frame


def authoritative_state_url(frame_url: str) -> str:
    parts = urlsplit(frame_url)
    parameters: list[tuple[str, str]] = []
    path_match = re.fullmatch(r"/c/([^/]+)", parts.path)
    if path_match is not None:
        parameters.append(("category", path_match.group(1)))
    parameters.extend(parse_qsl(parts.query, keep_blank_values=True))
    query = urlencode(parameters)
    return f"{STATE_URL}?{query}" if query else STATE_URL


def _authoritative_store_state(frame_url: str, timeout_ms: int) -> dict[str, Any]:
    url = authoritative_state_url(frame_url)
    with urlopen(url, timeout=max(timeout_ms / 1000, 0.001)) as response:  # noqa: S310
        return json.load(response)


def _assert_store_state(state: Mapping[str, Any], target: str, expected: str | None) -> None:
    if expected is None:
        raise AssertionError("Storefront state assertion requires an expected value")
    actual = state_value(state, target)
    if str(actual) != expected:
        raise AssertionError(
            f"Authoritative Storefront state {target!r} was {actual!r}, expected {expected!r}"
        )


def _assert_outcome(
    page,
    frame: Frame,
    assertion: EvaluationAssertion,
    store_state: Mapping[str, Any],
    timeout_ms: int,
) -> None:
    if assertion.kind == "panel_text":
        locator = page.locator(assertion.target)
        expect(locator).to_be_visible(timeout=timeout_ms)
        if assertion.expected is not None:
            expect(locator).to_have_text(assertion.expected, timeout=timeout_ms)
        return

    if assertion.kind == "url_matches":
        if re.search(assertion.target, frame.url) is None:
            raise AssertionError(f"URL {frame.url!r} did not match {assertion.target!r}")
        return

    if assertion.kind == "store_state":
        _assert_store_state(store_state, assertion.target, assertion.expected)
        return

    locator = frame.locator(assertion.target)
    if assertion.kind == "element_visible":
        expect(locator).to_be_visible(timeout=timeout_ms)
        if assertion.expected is not None:
            expect(locator).to_have_text(assertion.expected, timeout=timeout_ms)
    elif assertion.kind == "element_spotlighted":
        expect(locator).to_have_attribute(
            "data-copilot-spotlight",
            assertion.expected or re.compile(".+"),
            timeout=timeout_ms,
        )


def run_evaluation(
    browser_type: BrowserType,
    cases: tuple[EvaluationCase, ...],
) -> list[EvaluationResult]:
    browser = browser_type.launch(headless=True)
    results: list[EvaluationResult] = []
    try:
        for case in cases:
            started = time.perf_counter()
            deadline = started + (case.timeout_ms / 1000)
            context = browser.new_context()
            page = context.new_page()
            step_count = 0

            def count_action_result(request) -> None:
                nonlocal step_count
                if request.method == "POST" and request.url.endswith("/action-results"):
                    step_count += 1

            page.on("request", count_action_result)
            failure: str | None = None
            try:
                _reset_storefront(remaining_timeout_ms(deadline))
                page.goto(
                    PANEL_URL,
                    wait_until="domcontentloaded",
                    timeout=remaining_timeout_ms(deadline),
                )
                page.locator("#shopper-message").fill(
                    case.message, timeout=remaining_timeout_ms(deadline)
                )
                page.get_by_role("button", name="إرسال").click(
                    timeout=remaining_timeout_ms(deadline)
                )
                if case.expected_status == "complete":
                    expected_status = "اكتملت المهمة" if case.language == "ar" else "Task complete"
                    expect(page.locator("#task-status")).to_have_text(
                        expected_status, timeout=remaining_timeout_ms(deadline)
                    )
                frame = _frame_for_storefront(page)
                store_state = _authoritative_store_state(frame.url, remaining_timeout_ms(deadline))
                for assertion in case.assertions:
                    _assert_outcome(
                        page,
                        frame,
                        assertion,
                        store_state,
                        remaining_timeout_ms(deadline),
                    )
                remaining_timeout_ms(deadline)
            except Exception as error:  # Playwright failures must become case results
                if time.perf_counter() >= deadline:
                    failure = (
                        "TimeoutError: Evaluation Case exceeded its configured "
                        f"timeout of {case.timeout_ms}ms"
                    )
                else:
                    failure = f"{type(error).__name__}: {error}"
            elapsed_ms = (time.perf_counter() - started) * 1000
            results.append(
                EvaluationResult(
                    case_id=case.case_id,
                    passed=failure is None,
                    step_count=step_count,
                    elapsed_ms=elapsed_ms,
                    failure=failure,
                )
            )
            context.close()
    finally:
        browser.close()
    return results


def main() -> int:
    with local_services(), sync_playwright() as playwright:
        results = run_evaluation(playwright.chromium, DISCOVERY_CASES)
    for result in results:
        print(json.dumps(result.as_dict(), ensure_ascii=False))
    return 0 if all(result.passed for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
