"""Ticket 05 browser cases: a two-step message becomes a visible, ticking checklist.

The model is scripted (no network); see eval/plan_fixture_app.py. The model's own words for
each step come from the script, so these cases test plan execution, not language accuracy.
"""

from playwright.sync_api import expect, sync_playwright

from eval.browser_http import browser_post
from eval.plan_fixture_app import (
    ADD_STEP,
    ADD_STEP_2,
    ADD_THEN_CART,
    ADD_THEN_PANTS,
    ADD_THEN_TOO_MANY_THEN_CART,
    ADVICE,
    CART_STEP,
    PANTS_STEP,
    TOO_MANY_STEP,
)
from eval.services import local_services

TRACK_INPUT = """() => {
    const input = document.querySelector('#shopper-message');
    window.__inputStates = [];
    new MutationObserver(() => window.__inputStates.push(input.disabled)).observe(
        input, { attributes: true, attributeFilter: ['disabled'] }
    );
}"""


def open_product_page(page):
    browser_post(page, "http://localhost:4000/__test/reset")
    page.goto("http://localhost:4100")
    expect(page.locator("#shopper-message")).to_be_enabled()
    frame = page.frame_locator("#storefront-frame")
    frame.locator("body").evaluate("() => { location.href = '/p/shoe-01'; }")
    expect(frame.locator("#product-size")).to_be_visible()
    frame.locator("#product-size").select_option("42")
    frame.locator("#product-color").select_option("black")
    return frame


def send(page, message):
    page.evaluate(TRACK_INPUT)
    page.locator("#shopper-message").fill(message)
    page.get_by_role("button", name="إرسال", exact=True).click()


def marks(page):
    return page.locator("#plan-checklist li").evaluate_all("els => els.map(e => e.dataset.mark)")


def plan_requests(page):
    return page.request.get("http://localhost:8000/__eval/plan-requests").json()


def assert_input_stayed_disabled_until_the_plan_finished(page):
    expect(page.locator("#shopper-message")).to_be_enabled()
    states = page.evaluate("() => window.__inputStates")
    # Disabled when the plan started, enabled exactly once at the very end: never between steps.
    assert states and states[0] is True and states[-1] is False
    assert states.count(False) == 1, states


def test_two_step_sequence_shows_a_ticking_checklist_and_runs_both_steps_in_order():
    with local_services(agent_app="eval.plan_fixture_app:app"), sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            frame = open_product_page(page)
            send(page, ADD_THEN_CART)

            checklist = page.locator("#plan-checklist")
            expect(checklist).to_be_visible(timeout=15000)
            expect(checklist.locator("ol > li")).to_have_count(2)
            expect(checklist.locator("li").nth(0)).to_contain_text(ADD_STEP)
            expect(checklist.locator("li").nth(1)).to_contain_text(CART_STEP)
            expect(page.locator("#shopper-message")).to_be_disabled()

            expect(checklist.locator("li").nth(0)).to_have_attribute(
                "data-mark", "done", timeout=15000
            )
            expect(checklist.locator("li").nth(1)).to_have_attribute(
                "data-mark", "done", timeout=15000
            )
            assert marks(page) == ["done", "done"]

            expect(frame.get_by_role("heading", name="السلة")).to_be_visible(timeout=15000)
            assert frame.locator("body").evaluate("() => location.pathname") == "/cart"
            lines = page.request.get("http://localhost:4000/cart/state").json()["lines"]
            assert [(line["product_id"], line["quantity"]) for line in lines] == [("shoe-01", 1)]
            assert (lines[0]["size"], lines[0]["color"]) == ("42", "black")

            assert_input_stayed_disabled_until_the_plan_finished(page)

            requests = plan_requests(page)
            assert [r["message"] for r in requests] == [ADD_THEN_CART, CART_STEP]
            assert requests[0]["plan_step"] is None
            assert requests[1]["plan_step"] == {
                "position": 2,
                "of": 2,
                "earlier_steps_done": True,
            }
            # One plan only: the second step's own interpretation never makes a nested plan.
            assert page.locator("#plan-checklist ol").count() == 1
            assert page.locator("#plan-checklist li").count() == 2
        finally:
            browser.close()


def test_unrelated_pair_adds_once_then_shows_suggestions_with_retrieval_on():
    with local_services(agent_app="eval.plan_fixture_app:retrieval_app"), sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            open_product_page(page)
            send(page, ADD_THEN_PANTS)

            checklist = page.locator("#plan-checklist")
            expect(checklist.locator("ol > li")).to_have_count(2, timeout=15000)
            expect(checklist.locator("li").nth(0)).to_contain_text(ADD_STEP_2)
            expect(checklist.locator("li").nth(1)).to_contain_text(PANTS_STEP)
            expect(checklist.locator("li").nth(0)).to_have_attribute(
                "data-mark", "done", timeout=15000
            )
            expect(checklist.locator("li").nth(1)).to_have_attribute(
                "data-mark", "done", timeout=15000
            )
            assert marks(page) == ["done", "done"]

            # Step 2 is a search/recommend: its suggestions are on screen.
            expect(page.get_by_text(ADVICE, exact=True)).to_be_visible()
            expect(page.locator('[data-product-id="shoe-09"]')).to_be_visible()

            lines = page.request.get("http://localhost:4000/cart/state").json()["lines"]
            assert [(line["product_id"], line["quantity"]) for line in lines] == [("shoe-01", 1)]

            assert_input_stayed_disabled_until_the_plan_finished(page)

            requests = plan_requests(page)
            # On a product page the entry point is the action interpreter: step 1 is one intent
            # call that names the steps. Step 2 is interpreted at its turn, marked position 2,
            # and its search is handed back to the catalogue decision loop (same marker).
            assert [(r["prompt"], r["message"], r["plan_step"]) for r in requests[:2]] == [
                ("intent-v35", ADD_THEN_PANTS, None),
                ("intent-v35", PANTS_STEP, {"position": 2, "of": 2, "earlier_steps_done": True}),
            ]
            decisions = requests[2:]
            # search, then recommend (its advice text rides in the decision: no advice call).
            assert [r["prompt"] for r in decisions] == ["catalogue-decision-v9"] * 2
            assert all(r["message"] == PANTS_STEP for r in decisions)
            assert all(r["plan_step"]["position"] == 2 for r in decisions)
            assert page.locator("#plan-checklist li").count() == 2
        finally:
            browser.close()


REFUSED_EDIT_REPORT = (
    "وقفت عند خطوة ماتمّتش:\n"
    f"✓ {ADD_STEP}\n"
    f"✕ {TOO_MANY_STEP} — مش متأكد إذا تعديل السلة اكتمل. راجع السلة الحالية؛ مش هكرره تلقائيًا.\n"
    f"– {CART_STEP} (اتخطّت)"
)


def test_a_refused_cart_edit_midway_stops_the_plan_reports_it_and_rolls_nothing_back():
    with local_services(agent_app="eval.plan_fixture_app:app"), sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            posts = []
            page.on(
                "request",
                lambda request: posts.append(request.url) if request.method == "POST" else None,
            )
            frame = open_product_page(page)
            send(page, ADD_THEN_TOO_MANY_THEN_CART)

            checklist = page.locator("#plan-checklist")
            expect(checklist.locator("ol > li")).to_have_count(3, timeout=15000)
            expect(checklist.locator("li").nth(0)).to_have_attribute(
                "data-mark", "done", timeout=15000
            )
            # Step 1's add is in the cart and its 10-second Undo was offered.
            offered = page.request.get("http://localhost:4000/cart/state").json()["undo"]
            assert offered is not None and offered["remaining_ms"] > 0

            expect(checklist.locator("li").nth(1)).to_have_attribute(
                "data-mark", "failed", timeout=20000
            )
            expect(checklist.locator("li").nth(2)).to_have_attribute("data-mark", "skipped")
            assert marks(page) == ["done", "failed", "skipped"]

            # The report is one message in the Shopper's language; no Retry or question waits.
            expect(page.locator("#conversation li").last).to_contain_text("وقفت عند خطوة ماتمّتش")
            assert page.locator("#conversation li").last.text_content() == REFUSED_EDIT_REPORT
            expect(page.locator("#task-status")).to_have_text("وقفت عند خطوة ماتمّتش:")
            expect(page.locator("#retry-task")).to_have_count(0)
            expect(page.locator("#pending-question button")).to_have_count(0)
            expect(page.locator("#shopper-message")).to_be_enabled()

            # Nothing was rolled back and step 3 never ran: the line is still in the cart and
            # the page never went to the cart.
            lines = page.request.get("http://localhost:4000/cart/state").json()["lines"]
            assert [(line["product_id"], line["quantity"]) for line in lines] == [("shoe-01", 1)]
            assert frame.locator("body").evaluate("() => location.pathname") == "/p/shoe-01"
            assert [r["message"] for r in plan_requests(page)] == [
                ADD_THEN_TOO_MANY_THEN_CART,
                TOO_MANY_STEP,
            ]

            # No request is made after the failure.
            made = len(posts)
            page.wait_for_timeout(1500)
            assert len(posts) == made
        finally:
            browser.close()
