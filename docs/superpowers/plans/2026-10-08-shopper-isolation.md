# Shopper Isolation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for native execution, or superpowers:subagent-driven-development if the owner chooses delegation. Steps use checkbox syntax for tracking.

**Goal:** Isolate each browser shopper's commerce state and Agent authority before exposing the Controlled Storefront publicly.

**Architecture:** The Storefront owns opaque-cookie shopper records and individual GuardedCart instances. A challenge-bound, single-use ticket links an independently authenticated Agent browser to the Storefront shopper through authenticated private service calls. HTTP/SSE adapters enforce ownership; existing task transitions retain their safety checks.

**Tech Stack:** Existing Express/TypeScript, FastAPI/Python, browser Fetch/postMessage/EventSource, Vitest/Supertest and pytest/Playwright. No new service, database or authentication dependency.

**Spec:** [Approved shopper isolation design](../specs/2026-10-07-shopper-isolation-design.md).

**Status:** ready for owner plan review and execution-method selection; no implementation changes yet. Recommended method: native implementation in this session, followed by separate Spec and Standards reviews. The tasks share security-sensitive interfaces, so implement them sequentially rather than in parallel.

## Global constraints

- "No shopper may read, clear, confirm, resume, stop or take over another shopper's work, even if they know its identifiers."
- "Cart state must outlive a Copilot task and Start over must not empty it."
- "Tabs in the same browser profile share that shopper's cart; another browser profile/private context/device is independent."
- "Cookie values, link tickets and service credentials must not enter LLM context, conversations, event URLs, logs or evaluation traces."
- "Missing service configuration fails closed."
- "No live LLM is needed to prove isolation."
- Preserve ten-second Undo, thirty-minute task expiry, existing safety invariants and explicit tab takeover. No prompts, phrase rules, provider limits, AWS resources or paid calls change.
- Preserve unrelated dirty files. Scope commits explicitly; do not stage the existing AGENTS/plan edits, proposal files or previously untracked documents.
- The final code must remain local-only until public HTTPS, abuse controls, the durable global inference allowance and cloud model qualification are separately complete.

## Review focus

1. Two shoppers have the same product and cart revision: copied Undo/Confirmation/operation identifiers still cannot affect the other's cart (Tasks 1 and 3).
2. Two tabs begin linking simultaneously, or a ticket redemption response is lost: no silent identity replacement or replay of a pending Action (Tasks 2 and 4).
3. One service restarts while the other and an SSE stream survive: reject old commerce authority and stop private delivery; preserve a surviving cart after Agent-only restart (Tasks 3 and 5).
4. Cookies are deleted or expire while session IDs remain in localStorage: show a fresh-session/reset path without restoring someone else's data (Tasks 3 and 4).
5. Registry capacity is exhausted or a shopper floods fresh challenges: reject new admission without evicting active shoppers or growing unbounded state (Tasks 1–3).

## Shared contract and file boundaries

The following names are implementation contracts, not new LLM/domain vocabulary. All identifiers use cryptographically random 32-byte opaque values. Store a digest for browser/ticket bearer credentials where practicable; never log them.

```typescript
// store/src/shopper-state.ts
export interface ShopperBinding {
  shopper_id: string;
  generation: string;
}
export interface ShopperState {
  binding: ShopperBinding;
  cart: GuardedCart;
  loggedIn: boolean;
  lastActivity: number;
}
export class ShopperRegistry {
  constructor(options: {
    clock: () => number;
    capacity: number;
    ttlMs: number;
  });
  create(): { credential: string; state: ShopperState };
  resolve(credential: string): ShopperState | undefined;
  lookup(binding: ShopperBinding): ShopperState | undefined;
}
// store/src/shopper-link.ts
export interface LinkGrant extends ShopperBinding {
  challenge: string;
  audience: string;
}
export class LinkTickets {
  issue(binding: ShopperBinding, challenge: string, audience: string): string;
  redeem(
    ticket: string,
    challenge: string,
    audience: string,
  ): LinkGrant | undefined;
}
```

```python
# agent/shopper_access.py
@dataclass(frozen=True)
class ShopperBinding:
    shopper_id: str
    generation: str

# agent/storefront_service.py — private base URL comes from configuration, never Snapshot
class StorefrontService:
    async def redeem(self, ticket: str, challenge: str) -> ShopperBinding: ...
    async def validate(self, binding: ShopperBinding) -> bool: ...
    def register_confirmation(
        self, binding: ShopperBinding, snapshot_url: str,
        token: str, task_id: str, kind: str, cart_revision: int,
    ) -> bool: ...
```

Retain the synchronous confirmation-registration seam in task execution; the concrete client uses a bounded HTTP timeout. Background interpretation must revalidate ownership before publishing a result or Action, not merely when accepting the request. Service methods are injectable so unit tests need no real network. HTTP production paths never accept an unbound session even if pure domain tests construct one.

Runtime configuration uses `COPILOT_SERVICE_SECRET`, explicit public Panel/Storefront origins, a private Storefront base URL, and an explicit evaluation flag. No insecure default secret. Generate local configuration under ignored `work/` using an explicit helper; restrict file access, never print values, and pass it only to server processes. Use different Storefront and Agent cookie names because localhost ports share a cookie namespace. Production config rejects non-HTTPS public origins; local mode permits only the exact configured loopback origins. Do not infer trust from arbitrary Host or forwarded headers.

Initial explicit limits: 100 Storefront shoppers; twenty-four-hour inactivity lifetime; 100 Agent browser records; maximum eight active Agent sessions per browser; four outstanding challenges per browser; ticket/challenge lifetime sixty seconds; maximum 400 outstanding Storefront tickets and four per shopper. Expire before checking capacity, reject excess with 429/503, and never evict a still-active owner. Expiry is activity-based and independently clock-injectable; passive SSE delivery does not indefinitely extend shopper lifetime. These are conservative demo defaults, not measured public capacity.

## Task 1: Storefront-owned commerce state

**Files:** Create `store/src/shopper-state.ts`, `store/src/shopper-http.ts`, `store/tests/shopper-isolation.test.ts`; modify `store/src/app.ts`, `store/src/views.ts`, `store/public/cart.js`, `store/tests/reversible-cart.test.ts`, `store/tests/guarded-mutations.test.ts`, `store/tests/health.test.ts` and affected fixture consumers. Keep `GuardedCart` mutation policy intact.

**Interfaces:** Produce `ShopperRegistry` and request resolution from the shared contract. `cartView(cart: GuardedCart)` takes the request's cart explicitly. Browser state-changing routes require a valid cookie and exact allowed Origin plus an unpredictable browser CSRF token; missing identity on a write never silently creates a new cart. A safe bootstrap/navigation can issue a new shopper credential.

- [ ] Add failing HTTP tests using two persistent Supertest agents; replace old tests' cookie-free request sequences with authenticated browser fixtures. Seed routes operate only on that fixture's shopper.

```typescript
const a = request.agent(app),
  b = request.agent(app);
await a.get("/");
await b.get("/");
// The helper reads the browser CSRF token; it never supplies a shopper ID.
await add(a, { product_id: "shoe-09", size: "43", color: "blue", quantity: 1 });
expect((await b.get("/cart/state")).body.lines).toEqual([]);
const own = await a.get("/cart/state");
const denied = await mutate(b, "/cart/undo", {
  revision: own.body.revision,
  undo_id: own.body.undo.id,
  operation_id: "copied",
});
expect(denied.status).toBe(409);
expect((await a.get("/cart/state")).body.lines).toHaveLength(1);
```

Define test helpers `add(client, line)` to read current revision and call `mutate`; `mutate(client, path, body)` supplies the fixture's CSRF token and configured Storefront Origin. Repeat the attack when both carts have matching revisions and variants. Assert stale writes, copied Confirmations, independent login/logout state, private order URLs, expiry and full-capacity denial.

- [ ] Run `pnpm --filter @shopping-copilot/store test -- shopper-isolation`; confirm failure is shared/unauthorized state, not a setup error.
- [ ] Implement registry and HTTP ownership middleware. Bind all cart, checkout and order routes to the resolved request state, set personalized responses `Cache-Control: no-store`, and reject foreign Origin/invalid CSRF before mutation.
- [ ] Split manual Confirmation issuance into an authenticated browser route that generates its own token and permits only supported manual actions on the current cart. Update the existing clear-cart dialog without bypassing revision/expiry/one-use validation. Reserve Agent registration for Task 2's private route.
- [ ] Render completed fictional orders from the owned cart. Preserve any required demonstration-history fixtures only as explicitly labelled per-shopper copies. Do not invent real order history.
- [ ] Run Storefront tests and `pnpm --filter @shopping-copilot/store build`. Confirm registry TTL/capacity behavior with an injected clock. Record changed fixture assumptions; never add an auth bypass to restore old tests.

## Task 2: Linking and private service boundary

**Files:** Create `store/src/shopper-link.ts`, `store/src/service-auth.ts`, `store/tests/shopper-link.test.ts`, `agent/storefront_service.py`, `agent/tests/test_storefront_service.py`, `scripts/init_local_identity.py`; modify `store/src/app.ts`, `store/src/server.ts`, `eval/services.py`, `eval/tests/test_services.py`, `.env.example` only for placeholders, and local startup instructions.

**Interfaces:** Produce the shared ticket/client contracts. Browser `POST /__copilot/link-ticket` accepts `{challenge, audience}` with the Storefront cookie/CSRF and exact Panel audience. Private routes `/__internal/link/redeem`, `/__internal/shopper/validate`, `/__internal/confirmations` authenticate the service secret using constant-time comparison before parsing ownership data. Responses expose only binding/status to the trusted caller; expired/missing owner never creates state.

- [ ] Add failing ticket tests and private-route denial tests.

```typescript
const ticket = tickets.issue(owner.binding, "challenge-a", panelOrigin);
expect(tickets.redeem(ticket, "challenge-b", panelOrigin)).toBeUndefined();
expect(tickets.redeem(ticket, "challenge-a", panelOrigin)?.shopper_id).toBe(
  owner.binding.shopper_id,
);
expect(tickets.redeem(ticket, "challenge-a", panelOrigin)).toBeUndefined();
```

Also reject wrong audience, sixty-second expiry, stale generation, missing/wrong service secret and registry overflow. A failed mismatched redemption must not yield or mutate another owner's state. Define whether invalid attempts consume the ticket consistently; the positive test above requires mismatch to leave it unused.

- [ ] Run the focused Storefront link tests and `python -m pytest agent/tests/test_storefront_service.py` using `.venv/Scripts/python.exe` on Windows; capture expected failures.
- [ ] Implement service/config modules with fixed configured destinations, bounded timeouts and strict response parsing. Validate the shopper generation/liveness on every private operation. Confirmation registration validates the public Snapshot origin separately; never fetch a Snapshot-supplied backend URL.
- [ ] Implement the explicit local secret initializer with exclusive file creation, restricted permissions and no secret stdout. Inject an ephemeral shared secret into scripted evaluation subprocesses. Normal startup never enables `__test` routes; evaluation enables them explicitly. Ensure service secret/config never reaches Vite's public environment or browser bundles.
- [ ] Repeat focused tests, Ruff on changed Python modules and TypeScript builds. Document fail-closed startup and private-route proxy exclusion for later deployment.

## Task 3: Agent authorization and stream lifetime

**Files:** Create `agent/shopper_access.py`, `agent/shopper_http.py`, `agent/tests/test_shopper_access.py`; modify `agent/app.py`, `agent/session_state.py`, `agent/session_registry.py`, `agent/sessions.py`, `agent/task_runtime.py`, `agent/task_commands.py`, `agent/session_stream.py` and affected API tests.

**Interfaces:** Agent bootstrap issues its distinct HttpOnly cookie, CSRF token and challenge. Agent link accepts `{ticket, challenge}`, requires its own cookie/CSRF, redeems through `StorefrontService` and binds the resulting `ShopperBinding` to that browser. Add `shopper: ShopperBinding | None` to Session; HTTP-created sessions always set it. Pass this binding explicitly into the confirmation registrar; never use process-global current-owner state or rely on a task ID reverse lookup.

- [ ] Add failing route-matrix tests with two independently bootstrapped cookie jars and injected service client.

```python
for suffix in ["state?tab_id=known", "events?once=true&tab_id=known"]:
    response = browser_b.get(f"/sessions/{a_session}/{suffix}")
    assert response.status_code == 404
    assert "narration" not in response.text
assert browser_b.post(
    f"/sessions/{a_session}/takeover", json={"tab_id": "known"},
    headers=b_csrf_headers,
).status_code == 404
```

The test fixture performs the real access adapter flow against a deterministic injected Storefront client. Extend the matrix to messages, answers, action-results, retry, reconcile and Stop, with correctly shaped bodies so rejection cannot be mistaken for schema validation. Assert no changes to the victim and no model invocation. Cover deleted cookies, expired binding, wrong Origin/CSRF, simultaneous challenges and no silent replacement of an existing binding.

- [ ] Run `python -m pytest agent/tests/test_shopper_access.py` and see ownership failures.
- [ ] Implement access adapters and session binding. Enforce session ownership before lease checks; stranger sessions always return 404. Same-owner expired sessions may preserve existing 410 recovery behavior. Maintain existing tab takeover semantics only within an authorized shopper.
- [ ] Protect speech endpoints with browser identity/CSRF too, without invoking a paid transcriber in tests. Gate scripted `/step` and test-clock routes to explicit evaluation mode.
- [ ] Validate Storefront ownership before session operations, before publishing asynchronous model results and at each SSE delivery batch. SSE must close on revocation/expiry/service-generation loss; no indefinite polling after denial. Handle private-service failure as unavailable without replay or automatic mutation retry. Bound service validation frequency for idle streams without caching positive authority for a mutation.
- [ ] Add tests for revocation during an open stream and during an in-flight interpretation. Block completion with an event-controlled fake LLM, revoke ownership, then release it and assert no Action is published. Validate separate 24-hour browser/shopper and 30-minute task lifetimes, capacity and cleanup.
- [ ] Run focused API/guarded/recovery tests, Ruff and typechecks. Update old tests to use authenticated fixtures without weakening production checks or hiding new tests behind an autouse bypass.

## Task 4: Browser linking, recovery and credentials

**Files:** Create `panel/src/shopper-link.ts`, `panel/tests/shopper-link.test.ts`; modify `panel/src/main.ts`, `panel/src/panel.ts`, `panel/src/event-stream.ts`, `bridge/src/runtime.ts`, `bridge/src/types.ts` and corresponding Bridge/Panel tests.

**Interfaces:** `linkShopper(): Promise<void>` completes bootstrap/challenge/ticket redemption before `PanelController.start()`. Define infrastructure-only `shopper_link_request` and `shopper_link_result` messages with request correlation IDs; both sides check exact origin and source window. These messages never enter Snapshot, ActionResult, history or model context.

- [ ] Add failing browser-channel tests for forged source/origin, duplicate/late response, wrong correlation ID and timeout.

```typescript
window.dispatchEvent(
  new MessageEvent("message", {
    origin: "https://untrusted.example",
    source: window,
    data: {
      type: "shopper_link_result",
      request_id: expectedId,
      ticket: "fake",
    },
  }),
);
expect(agentLink).not.toHaveBeenCalled();
```

Test normal linking before session restore, two-tab challenges, expired ticket retry via a fresh challenge and lost redemption response. Retrying infrastructure linking must not replay a shopping command. Helpers use fake HTTP/channel adapters, not real credentials.

- [ ] Run focused Panel/Bridge tests; capture the failing behavior.
- [ ] Implement credentials-included fetch and credentialed EventSource with exact CORS configuration. Keep CSRF/link credentials only in memory, not URL/localStorage. Any CSRF metadata or hidden form fields are infrastructure data explicitly excluded from Snapshot/model serialization; test that exclusion. Serialize first bootstrap in same-profile tabs or reconcile cookie races safely before controller startup. Link retries are bounded and leave visible retry/reset UI on failure.
- [ ] Preserve cart on Copilot Start over, reject stale saved session IDs after identity loss, and retain refresh/Snapshot reconciliation for valid ownership. A reset must not automatically submit the previous message or Action.
- [ ] Run Panel/Bridge tests and workspace builds. Verify no service credential or link ticket appears in built assets, saved session data or emitted model Snapshot payloads.

## Task 5: End-to-end isolation, failures and release evidence

**Files:** Create `eval/tests/test_shopper_isolation.py`; modify affected browser fixture setup in `eval/tests/` and `eval/services.py`, `README.md`, `docs/system-analysis-design.md`, `docs/cap04-credit-only-plan.md`, `PROJECT_CHECKPOINT.md` and `handoff.md` only where implementation/evidence changes.

**Interfaces:** Use the existing `local_services()` lifecycle with scripted provider, explicit evaluation routes and ephemeral service authentication. Each browser fixture performs normal bootstrap and owns its seed/reset calls. Cross-context setup must never rely on a global cart reset.

- [ ] Add the focused real-browser test with two Playwright contexts and independent cookie jars.

```python
with browser.new_context() as shopper_a, browser.new_context() as shopper_b:
    a, b = shopper_a.new_page(), shopper_b.new_page()
    for page, quantity in [(a, "1"), (b, "3")]:
        page.goto("http://localhost:4100")
        frame = page.frame_locator("#storefront-frame")
        expect(frame.locator("h1")).to_have_text("تسوّق بسهولة")
        frame.locator("body").evaluate("() => { location.href = '/p/shoe-09'; }")
        frame.locator("#product-size").select_option("43")
        frame.locator("#product-color").select_option("blue")
        frame.locator('input[name="quantity"]').fill(quantity)
        frame.locator('[data-testid="add-to-cart"]').click()
        expect(frame.locator("#cart-feedback")).to_have_text("تمت الإضافة إلى السلة")
    assert a.request.get("http://localhost:4000/cart/state").json()["lines"][0]["quantity"] == 1
    assert b.request.get("http://localhost:4000/cart/state").json()["lines"][0]["quantity"] == 3
    a.reload()
    assert a.request.get("http://localhost:4000/cart/state").json()["lines"][0]["quantity"] == 1
```

Use `frame_locator` and existing product/cart test IDs; add user-visible checkout, own-order history, cross-owner order/session attacks, same-profile tab takeover and Start over assertions. Test copied Undo and Confirmation against equal-revision carts. Record no private credential payloads in traces.

- [ ] Add controlled Agent-only and Storefront-only restart cases to the existing service lifecycle helper. Agent restart preserves Storefront cart but needs new Agent authority. Storefront restart invalidates links and closes old streams; old Confirmation, Undo and ActionResult never affect fresh state. Include browser-cookie deletion, TTL advance and registry-capacity exhaustion.
- [ ] Run `python -m pytest eval/tests/test_shopper_isolation.py` with local services stopped; the harness refuses occupied ports. Inspect actual browser behavior, not just endpoint success codes.
- [ ] Run repository checks once after focused tests pass:

```powershell
pnpm format:check:ts
.venv/Scripts/python.exe -m ruff format --check agent eval
pnpm lint:ts
.venv/Scripts/python.exe -m ruff check agent eval
pnpm --recursive test
.venv/Scripts/python.exe -m pytest agent/tests eval/tests
pnpm --recursive build
```

These are the Makefile CI components with the explicit Windows Python path. Report any infrastructure failure honestly and rerun only affected checks after diagnosis; do not claim an uninterrupted clean run if it was not one.

- [ ] Use the `code-review` skill for separate Spec and Standards reviews of the complete implementation diff. Resolve all actionable findings and rerun affected safety tests. No runtime completion claim before this evidence.
- [ ] Update docs with implemented ownership/lifetime behavior and exact test outcomes, preserving unimplemented cloud gates. Check staged files for secrets and unwanted local artifacts. Stage only this work and commit locally; no push or deployment is implied.

## Commit boundaries and self-review

Commit a task only when its focused checks pass and intermediate runtime is coherent. Tasks 2–4 may need one integration commit because unpaired identity protocols must fail closed rather than leave a working public bypass. Do not deploy intermediate states. The final integrated commit follows full checks and both reviews.

Self-review: all spec acceptance groups map to Tasks 1–5. Owner binding, private confirmation registration, manual confirmation/CSRF, credential storage, personal orders, streaming revocation, dual lifetimes, capacity, test-route gating and both restart directions are explicitly covered. No prompt/phrase interpretation, account provisioning, persistent database or real-login feature is added. Public HTTPS and the durable global spending ledger remain separate CAP-04/deployment gates, not missing tasks in this isolation slice.
