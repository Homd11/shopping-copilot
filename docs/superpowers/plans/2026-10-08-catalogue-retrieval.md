# Catalogue Retrieval Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for native implementation, or superpowers:subagent-driven-development if the owner selects delegation. Execute task by task; steps use checkbox syntax.

**Goal:** replace runtime product arrays/full-catalogue Agent reads with one authoritative product repository and bounded model-directed retrieval, preserving advice and shopping safety.

**Architecture:** the Storefront owns SQLite and product queries. The Agent requests search/details through a fixed authenticated service, while a separate coordinator bounds model decisions and evidence. Existing browser Actions and cart authorization remain the execution boundary.

**Tech Stack:** pinned Node 24.13.0, built-in `node:sqlite`, FTS5, Express/TypeScript, existing Python/Pydantic/provider adapter, Vitest and pytest/Playwright. Optional local embedding dependencies are qualified separately from the lexical path.

**Spec:** [Approved catalogue retrieval design](../specs/2026-10-08-catalogue-retrieval-design.md), approved by the owner's “lets go” on 8 October 2026.

**Status:** owner approved native execution. Tasks 1–6 are implemented locally; Task 7 automated verification and reviews are complete. Live-model/default activation and whole-stack host qualification remain explicitly open. See [verification](../../catalogue-retrieval-verification.md).

## Global constraints

- “The model remains responsible for interpreting messy language, corrections, references, quantities and negation.” No phrase dictionaries, hardcoded typo fixes, semantic regex interpretation or keyword negation rules.
- “Search returns a broader evidence pool, not three preselected recommendations.” Three cards are a presentation limit after model selection.
- Maximum three model decision attempts per message, including initial interpretation and repairs; four executed read operations; one final advice completion. Exhausted attempts do not reset on Retry inside the same turn.
- Search query: 1,024 characters; at most twenty conjunctive predicates; ten summaries per page; nine details per call; 32 KiB serialized read response; 48 KiB accumulated retrieval evidence per model request. All sizes count UTF-8 bytes.
- Decimal Money; present/absent/unknown fact semantics; missing facts do not establish an exclusion. Preserve named unmet requirements on Alternatives.
- Preserve product IDs/routes/seed facts, shopper isolation, observed target checks, Confirmation, ten-second Undo, thirty-minute task expiry, Stop and uncertain-outcome recovery.
- No paid calls during ordinary implementation/tests, no budget increase, AWS resource, push, hosted vector service or unrelated refactor. Actual-model qualification remains open until explicitly budgeted; do not call it passed using scripted responses.
- Work from the existing isolated `codex/shopper-isolation` checkout after `7ec10c8`; preserve the original dirty `D:/agent depi` checkout. Commit each verified implementation slice locally.
- Read `CONTEXT.md`, current checkpoint/handoff, the approved spec and original local-MVP specification before implementation. Keep CAP-02/03 frozen datasets/results untouched.

## Execution evidence

Tasks 1–3, 5 and 6 have local implementation and regression evidence. Task 4 has
an exposed offline comparison and optional hybrid backend, but end-to-end CPU
latency and whole-stack memory qualification are still open. Task 7 has combined
browser/HTTP safety evidence and independent reviews; live-model evaluation and
default activation remain open. Checkbox completion below refers to implementation
work, not to the explicitly deferred live-model or deployment gates.

## Review focus

1. A product becomes unavailable or changes price after confirmation without a quantity change: reject the stale checkout, preserve the shopper's cart and show updated terms (Task 2).
2. “مش جلد” plus an omitted material fact: distinguish unknown from verified absence; do not let lexical/embedding similarity certify a match (Tasks 3 and 6).
3. A partially remembered name or cross-category outfit request matches a product outside the first three results: the model can retrieve and select it without a forced category (Tasks 4–6).
4. Stop, identity revocation or Storefront restart occurs during a search/model call: discard completion; no late recommendation, Action or repeated paid attempt (Tasks 5 and 7).
5. Multi-byte Arabic text, malicious FTS syntax, a repeated read, or a stale index/cursor: enforce limits without corruption, authority leakage, fabricated empty results or loops (Tasks 3–5).

## File boundaries and contracts

Keep money/product types in `store/src/catalogue.ts`; move seed declarations to `store/src/catalogue-seed.ts`. Do not duplicate product definitions across runtime modules.

| New file                                | Responsibility                                                                            |
| --------------------------------------- | ----------------------------------------------------------------------------------------- |
| `store/src/catalogue-db.ts`             | Schema, migration, connection lifetime, atomic import and revisions                       |
| `store/src/product-repository.ts`       | Current product lookups and existing Storefront filtering                                 |
| `store/src/catalogue-query.ts`          | Bounded query validation, parameterized filters, lexical/semantic ranking and eligibility |
| `store/src/catalogue-api.ts`            | Authenticated search/details HTTP serialization                                           |
| `store/scripts/catalogue-import.ts`     | Explicit seed import and offline export/index loading                                     |
| `protocol/catalogue/v1.json`            | Shared read JSON schemas and limits; separate from browser protocol v1                    |
| `agent/catalogue_client.py`             | Fixed-origin private HTTP reads, strict parsing, timeout/size errors                      |
| `agent/catalogue_retrieval.py`          | Read decisions, attempt accounting, turn-local evidence and cancellation                  |
| `agent/catalogue_embedding.py`          | Optional pinned CPU query encoder; no imports/downloads in lexical mode                   |
| `eval/catalogue_retrieval.py`           | Reproducible offline comparison and result artifact generation                            |
| `eval/datasets/catalogue-retrieval-v1/` | Exposed query groups, fact fixtures, relevance labels and freeze manifest                 |

Shared implementation shapes (define before consumers):

```typescript
// product-repository.ts; Product and ProductConstraints remain in catalogue.ts.
export interface ProductRepository {
  revision(): number;
  get(id: string): Product | undefined;
  filter(constraints: ProductConstraints): Product[];
}
// catalogue-query.ts; JSON forms are mirrored in protocol/catalogue/v1.json.
type Predicate =
  | { field: "price"; op: "gte" | "lte"; amount: string; currency: "EGP" }
  | {
      field: "category" | "product_type" | "color" | "size" | "feature" | "use";
      op: "eq" | "exclude";
      value: string;
    }
  | { field: "available"; op: "eq"; value: boolean };
type SearchQuery = {
  v: 1;
  query: string;
  predicates: Predicate[];
  requirements: Predicate[];
  unverified_requirements: string[];
  sort: "relevance" | "cheapest" | "newest";
  cursor: string | null;
};
// predicates narrow this read; requirements preserve the shopper's original
// eligibility conditions, including when the model investigates alternatives.
type RequirementResult = {
  index: number;
  status: "satisfied" | "violated" | "unknown";
};
type ProductEvidence = Product & {
  absent_features: string[];
  absent_uses: string[];
};
type Candidate = {
  product: ProductEvidence;
  product_revision: number;
  requirements: RequirementResult[];
};
type SearchResult = {
  v: 1;
  catalogue_revision: number;
  candidates: Candidate[];
  ranking: "lexical" | "hybrid";
  exact_count: number | null;
  next_cursor: string | null;
  truncated: boolean;
  unverified_requirements: string[];
};
type DetailsResult = {
  v: 1;
  catalogue_revision: number;
  products: Candidate[];
  missing_ids: string[];
};
```

The schemas bound all strings/arrays, reject extra fields, and serialize the existing camelCase Storefront Product consistently in both languages. `ProductEvidence` adds explicit negative facts; existing seeds import both negative arrays as empty. Contradictory positive/negative facts fail import. Search and details share that evidence shape; neither returns arbitrary HTML. Use stable per-requirement indices; unsupported attributes remain unknown. Across `predicates` and `requirements`, at most twenty distinct typed predicates are accepted; repeating the same condition in both does not count twice. `unverified_requirements` has at most twenty entries of at most 200 characters each and cannot confer exact eligibility.

The HTTP service returns errors with `code` from `invalid_query`, `stale_cursor`, `stale_index`, `record_too_large`, `unavailable`; never turn these into a successful zero-match response. Search/details calls use the existing private service credential and configured Storefront destination, not model-selected URLs.

## Task 1: SQLite repository and reproducible seed migration

**Create:** database/repository/seed/import files listed above; `store/tests/product-repository.test.ts`.
**Modify:** `store/src/catalogue.ts`, `store/package.json`, README startup instructions. Runtime consumers switch in Task 2; only seed import/tests may read the extracted seed array thereafter.
**Produces:** `openCatalogue(path: string): ProductRepository`, `importCatalogue(path: string, products: readonly Product[]): void`, `exportCatalogue(path: string): readonly Product[]`. Opening never seeds. Keep connection close available on the concrete repository for tests/shutdown.

- [x] Write a temporary-file database round-trip test and verify all existing seeds exactly, including Money strings, ordering used by category pages and the current independent size/color choice semantics. Add reopen, invalid-import rollback, idempotent reimport and missing-database tests.

  ```typescript
  importCatalogue(path, seedProducts);
  const repo = openCatalogue(path);
  expect(repo.get("shoe-01")).toEqual(
    seedProducts.find((p) => p.id === "shoe-01"),
  );
  const before = repo.revision();
  importCatalogue(path, seedProducts);
  expect(repo.revision()).toBe(before);
  ```

- [x] Run `pnpm --filter @shopping-copilot/store exec vitest run tests/product-repository.test.ts` and capture the intended missing-repository failure.
- [x] Implement products, variants, facts, revision metadata and FTS tables transactionally. Use stable imports, foreign keys and unique IDs. For SQL price comparison, store exact integer minor units and convert through BigInt; validate signed 64-bit storage bounds and retain original canonical decimal strings in the API. No floating-point money comparisons.

  ```typescript
  db.exec("BEGIN IMMEDIATE");
  try {
    // Bound prepared statements insert validated rows and matching FTS records.
    // Revision increments only if the canonical catalogue content changes.
    db.exec("COMMIT");
  } catch (error) {
    db.exec("ROLLBACK");
    throw error;
  }
  ```

- [x] Add `pnpm --filter @shopping-copilot/store exec tsx scripts/catalogue-import.ts --database <path>` with an ignored `work/catalogue.sqlite` default. Export and index-import modes are offline CLI modes, never public routes. Recheck SQLite/FTS on CI's pinned Node and document its experimental API status. Local read-only planning probe passed on Node 24.13.0; this is not repository implementation evidence.
- [x] Run repository and existing catalogue unit tests plus Storefront build. Commit `Introduce SQLite product repository and explicit seed import`.

## Task 2: One source for Storefront, cart checks and order facts

**Modify:** `store/src/app.ts`, `server.ts`, `views.ts`, `guarded-cart.ts`, `shopper-state.ts`, `shopper-link.ts`, `eval/services.py`, Storefront/evaluation fixtures.
**Test:** `store/tests/catalogue-freshness.test.ts`, existing cart/shopper suites.
**Consumes:** `ProductRepository`; inject the same instance into `createApp`, `ShopperRegistry` and each `GuardedCart`. Views receive product data/resolver explicitly; no hidden default seed repository.

- [x] Add a failing HTTP test: seed an owned cart, obtain checkout confirmation at displayed revision, import a changed price, submit the old confirmation, and assert rejection/no order with cart lines retained. Repeat for availability/variant removal and explicit known absence facts. Compare checkout and product-page prices from the same database.

  ```typescript
  const displayedRevision = cart.revision;
  expect(
    cart.register({
      token,
      task_id,
      kind: "submit_checkout",
      cart_revision: displayedRevision,
    }),
  ).toBe(true);
  importCatalogue(path, changedPriceProducts);
  expect(
    cart.consume(token, "submit_checkout", String(displayedRevision)),
  ).toBe(false);
  expect(cart.state.orders).toHaveLength(0);
  ```

- [x] Run the new freshness test, then replace every runtime array consumer with repository reads, including the temporary legacy catalogue export endpoint. Evaluation bootstraps a temporary database per Storefront service lifecycle; never seed the owner's persistent file.
- [x] Implement `GuardedCart.refreshProductTerms(): void`: detect changes to authoritative products referenced by the cart using their revisions, increment the cart revision and clear confirmations before rendering, registering, editing or consuming. Persist the catalogue revision in each confirmation as an additional conservative check. An import is atomic, and consume/check/order creation runs without an asynchronous gap. Thus existing `cart:<revision>` Snapshot/Action signatures detect changed terms without weakening the browser protocol.
- [x] Preserve Undo's original deadline; reconcile its operation revision when terms change, never extend it. Undo restores exact cart lines, not a promise of old prices/availability. Unavailable/deleted items can be removed; restoring an obsolete line produces a non-purchasable line whose checkout remains blocked. Never silently substitute a variant. Add these tests.
- [x] Store completed order line names, unit Money and chosen variants at submission; render those immutable facts after later catalogue edits. Keep fictional seed history clearly labelled. Add price-edit-after-order and two-shopper tests.
- [x] Run Storefront tests/build and Python isolation/cart/checkout browser tests serially. Commit `Use authoritative products throughout storefront commerce`.

## Task 3: Bounded search and detail service

**Create:** query/API/schema files listed above; `store/tests/catalogue-api.test.ts`, `protocol/catalogue/fixtures/`.
**Modify:** Storefront route composition and private service authentication reuse.
**Produces:** `POST /__internal/catalogue/search` with `SearchQuery`; `POST /__internal/catalogue/details` with `{v:1, ids:string[], requirements:Predicate[], unverified_requirements:string[]}`. Maximum nine distinct IDs; preserve requested order and report missing IDs.

- [x] Add HTTP contract tests using the real repository. Cover authentication, query/predicate/byte bounds, SQL/FTS syntax treated as data, negative facts, unknown facts, cross-category search, top-ten filtering, explicit price/newest ordering and stale pagination.

  ```typescript
  // An omitted feature must not satisfy a negative requirement.
  expect(unknownMaterial.requirements).toContainEqual({
    index: 0,
    status: "unknown",
  });
  expect(knownNoLeather.requirements).toContainEqual({
    index: 0,
    status: "satisfied",
  });
  expect(knownLeather.requirements).toContainEqual({
    index: 0,
    status: "violated",
  });
  expect(Buffer.byteLength(JSON.stringify(result), "utf8")).toBeLessThanOrEqual(
    32768,
  );
  ```

- [x] Run `pnpm --filter @shopping-copilot/store exec vitest run tests/catalogue-api.test.ts` and capture the missing-route failure. Implement bound predicates and quote user tokens before constructing FTS syntax. Unicode/case/spacing normalization is allowed; Arabic/Franco phrase mapping is not.
- [x] Apply structured conditions before top-k. Search may return unknown-evidence candidates for inspection but must label them; known contradictory required/excluded facts are not eligible recommendations. An explicit alternative read keeps the original `requirements`. Exact counts are null if semantic/unverified requirements prevent exhaustive certification.
- [x] Use an authenticated cursor bound to canonical query, catalogue revision and stable position. Invalid/stale cursor yields `stale_cursor`; no hidden query changes. Bound result construction before sending, set truncation/pagination explicitly, and reject an oversized single record. Test real multi-byte Arabic, not only ASCII length.
- [x] Share valid/invalid contract fixtures with the later Python client. Run focused service tests, Storefront build and formatting. Commit `Expose bounded authenticated catalogue reads`.

## Task 4: Compare retrieval and qualify the optional semantic path

**Create:** `eval/catalogue_retrieval.py`, `eval/tests/test_catalogue_retrieval.py`, retrieval dataset directory, `docs/catalogue-retrieval-evaluation.md`.
**Optional runtime files owned here:** `agent/catalogue_embedding.py`, `store/src/catalogue-semantic.ts`, an isolated optional dependency lock. Do not import `eval` modules into production.
**Consumes:** frozen export from Task 1, Task 3 search contract. **Produces:** versioned comparison artifacts and a documented lexical/hybrid runtime choice.

- [ ] Freeze forty exposed development queries (ten per language group) with conversation grouping, relevant IDs, typed constraints, unknown/exclusion labels and data provenance before tuning. Include the five Review Focus classes. Hash the source and labels; keep a separate 1,000-product synthetic load fixture. These are not CAP-02 unseen data and not human gold.
- [ ] Write failing metric tests on tiny explicit ranked lists, and tests for mismatched IDs/revisions/model hashes. Use the current discovery selector as the historical baseline and clearly disclose its three-item limit; run filtered FTS and hybrid candidates on the same queries, not a differently filtered subset.

  ```python
  assert recall_at_k(["p2", "p1"], {"p1", "p3"}, k=2) == 0.5
  assert reciprocal_rank(["p2", "p1"], {"p1"}) == 0.5
  # Both metric functions live in eval/catalogue_retrieval.py.
  ```

- [ ] Run the metric tests, then implement immutable per-query predictions, per-language recall@10/MRR, hard-constraint violations, unknown/no-match handling, latency and serialization size. Record real provider usage only when actually measured; offline tests must mark LLM cost/quality unmeasured. Record zero-relevance cases separately rather than awarding them arbitrary recall.
- [ ] Compare one pinned local semantic candidate: the already-used `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, revision `e8f8c211226b894fcb81acc59f3b34ba3efd5f42`. Reuse verified local weights if available; no provider call or unpinned remote code. Product vectors use catalogue text/facts only. Force CPU for deployment feasibility measurements; development GPU timings are separate.
- [ ] Implement a qualified hybrid path only through the same contract: offline CLI loads product vectors plus model/dimension/catalogue bindings into SQLite; the Agent optional encoder supplies a query vector in a private transport-only envelope. The model never supplies vectors. Storefront validates shape/finiteness/metadata, filters eligible products first, then ranks candidates with lexical/semantic reciprocal-rank fusion (`1/(60+rank)` per list) and stable-ID ties. Explicit price/newest sorts bypass relevance ordering. Direct ID details never depend on semantic search.
- [ ] Missing/stale vectors cannot be silently used. If configured hybrid dependencies/indexes are unavailable, return an explicit retrieval error; do not pretend an empty catalogue or silently switch backends. Lexical configuration imports no embedding packages and needs no downloaded weights. Add parity/invalid-vector/index-revision tests.
- [ ] Record selection from the fixed comparison: semantic retrieval must improve overall recall@10 without a per-language recall regression, keep all exclusion/freshness tests passing, and show p95 warm retrieval at most one second on the 1,000-product CPU fixture. Report process/whole-stack memory against the proposed 2 GiB host; runtime promotion additionally requires a measured stack fit with at least 512 MiB headroom. An unmeasured host fit leaves hybrid deployment unqualified. These are development selection gates, not general accuracy claims; do not retune them after seeing results.
- [ ] Run offline tests/comparison once, inspect errors and record limitations. If neither method meets quality/safety requirements, keep default activation open and present the evidence rather than add phrase rules. Commit `Evaluate and qualify bounded catalogue retrieval`.

## Task 5: Provider-neutral read coordinator

**Create:** `agent/catalogue_client.py`, `agent/catalogue_retrieval.py`, `agent/tests/test_catalogue_client.py`, `agent/tests/test_catalogue_retrieval.py`.
**Modify:** provider-independent request building only where necessary; reuse existing HTTP service configuration and accounting.
**Consumes:** Task 3 wire schemas and selected backend. **Produces:** `CatalogueClient.search(SearchQuery) -> SearchResult`, `CatalogueClient.details(ids, requirements, unverified_requirements) -> DetailsResult` as async methods; and `retrieve_products(message, context, llm, catalogue, ensure_active) -> RetrievalOutcome`.

`RetrievalOutcome` carries the final `StructuredIntent` or clarification, verified evidence, model-selected IDs, all attempt/read counts and explicit error/exhaustion status. `ensure_active` is an async callback checking the original task, shopper binding and cancellation. Pass existing attempt IDs to the existing model-accounting layer; do not add a second independent spend ledger.

- [x] Define the versioned JSON decision union in `catalogue_retrieval.py`: `search` with SearchQuery; `details` with IDs and original requirements; `finish` with existing StructuredIntent and at most three selected IDs; `clarify` with one bounded question. Persist the interpreted original requirements within the turn; a search's narrowed/relaxed predicates never overwrite them. Shopper corrections may replace requirements only through a new model interpretation of the new message.
- [x] Write tests with event-controlled scripted clients: search/details/refine succeeds within limits; direct non-shopping navigation finishes with no catalogue reads; the fourth decision attempt never starts; failed parses count; repeated same-revision queries reuse evidence; Stop/ownership loss discards a released completion.

  ```python
  # Scripted turns use the real coordinator and fake protocol clients, not phrase dispatch.
  assert outcome.decision_attempts <= 3
  assert outcome.read_operations <= 4
  assert len(outcome.selected_ids) <= 3
  assert len(serialized_evidence.encode("utf-8")) <= 49152
  ```

- [x] Run `python -m pytest agent/tests/test_catalogue_client.py agent/tests/test_catalogue_retrieval.py -q` and inspect intended failures. Implement strict shared schema parsing, fixed-origin/no-redirect requests, five-second read timeout, status/size errors, private credential handling and bounded UTF-8 evidence assembly. A JSON response cannot allocate an unbounded body before the size check.
- [x] Implement the shared attempt budget across interpretation/repair/refinement; reserve one of four reads for a final details refresh. The coordinator refreshes selected IDs after `finish`, then checks selection eligibility. References alone remain non-authorizing. Exhaustion returns available verified partial information or a clarification state without synthesizing a success claim.
- [x] Record content hashes/revisions for turn-local reuse. Use HTTP ETags bound to the canonical request and catalogue revision; the service returns 304 only after checking its current revision. This revalidation consumes one of the four read operations, even if it avoids a response body. Never reuse a stale price across turns or treat a repeated request as a free new attempt. Before/after each await invoke `ensure_active`. Do not store raw read bodies or credentials in telemetry. Test truncation, oversized records, stale-index errors and late async results.
- [x] Run focused Agent tests and Ruff. Commit `Add bounded model-directed catalogue read coordinator`.

## Task 6: Integrate discovery, product references and advice

**Modify:** `agent/app.py`, `agent/advice.py`, `agent/catalogue.py`, `agent/llm/intent_pipeline.py`, `agent/product_context.py`; task state/command interfaces only as required to carry outcome/evidence. **Test:** `agent/tests/test_catalogue_advice.py`, existing advice/semantic/cart suites.

- [x] Add failing integration tests where the scripted model selects a valid candidate outside the old first three, searches without a category, keeps an unknown attribute in the request, honors an exclusion and requests details of an earlier suggestion. Verify it does not need a specific spelling in code. Also pin ordinary quantity/account navigation paths and no extra retrieval calls.
- [x] Wire the coordinator into the existing task interpretation seam. Build a compact request from existing bounded conversation/cart/Snapshot plus read-capability descriptions. For retrieval, remove the full vocabulary whitelist and category-required rejection; retain schema/currency/bounds validation. Existing navigation/filter Actions must still use supported destinations/controls. Unknown requested facts remain unknown, not a fabricated supported filter.
- [x] Replace `prepare_advice` full-catalogue selection with `prepare_retrieved_advice(outcome: RetrievalOutcome) -> AdviceEvidence`, using fresh details and server-computed eligibility. Use model-selected IDs; remove neutral-palette/product-ID ranking and templated recommendation reasons from the new discovery path. Do not delete code still required by the frozen historical evaluation baseline; move that baseline into evaluation-only code when runtime no longer uses it.
- [x] Carry original hard requirements and unknowns into the final advice request and validate proposed IDs/eligibility before publishing cards. Model prose remains natural and subjective advice remains clearly opinion; schema checks alone are not evidence that every sentence is factual. Test grounded/unsupported claims via scripted contract checks and record prose fidelity in the later live evaluation.
- [x] Keep action execution on the existing protocol. Trusted retrieval can add observed catalogue identities to bounded known-product references, but opening/mutating still requires configured routes/current DOM targets and fresh state. Stop/restart/revocation prevents later advice or Actions. Update prompt/schema versions and provider-independent fixtures honestly.
- [x] Remove normal Agent full-catalogue reads only once all runtime consumers are migrated. Keep the database-backed compatibility path operational until this task is complete; it is the same source of truth, not a fallback array. Gate new Agent mode behind `CATALOGUE_RETRIEVAL_ENABLED` until Task 7 qualification, with default remaining current mode meanwhile.
- [x] Run new integration tests plus existing advice, semantic boundary, navigation, guarded mutation and recovery suites. Commit `Integrate catalogue retrieval with grounded shopping advice`.

## Task 7: End-to-end evidence and activation gate

**Create:** `eval/tests/test_catalogue_retrieval_browser.py`, `docs/catalogue-retrieval-verification.md`.
**Modify:** README, checkpoint/handoff, design status and evaluation fixture setup. Update `.env.example` with placeholders/feature switches only.

- [ ] Add browser cases using scripted model decisions through real authenticated service routes: cross-category advice → selected product → add; named comparison → quantity change with several cart lines; exclusion/unknown material; stale price confirmation; service failure; Stop during read; two independent shoppers. Observe actual cart/order results, not only narration.

  ```python
  # The browser owns authentication; the service harness supplies ephemeral credentials.
  assert shopper_a_cart != shopper_b_cart
  assert mutation_count == 1
  assert old_confirmation_rejected
  assert order_unit_price == price_at_submission
  ```

- [x] Run focused browser cases with no other harness holding the service ports. Then run the existing repository CI commands once after fixes: Prettier, ESLint, Ruff check/format, recursive TypeScript tests/builds, test-inclusive Bridge/Panel typechecks, and `python -m pytest agent/tests eval/tests`. Use `D:/agent depi/.venv/Scripts/python.exe` on this host. Inspect every exit code; distinguish clean full runs from focused rerun evidence.
- [ ] Prepare a bounded live evaluation from the frozen messy queries with grouped follow-ups and traceable product evidence. Before any provider call, inspect remaining authorized allowance without printing the key; prior capped acceptance authorizations are not blanket permission for new paid experiments. If a specific allowance is not already approved, present the concrete cost/call cap for approval and leave live qualification open. Do not consume funds merely to complete the checklist.
- [ ] Record actual decisions, retrieval recall, requirement preservation, prose grounding, unknown handling, tokens/calls, latency and failures. Default activation requires the spec's real-model gate as well as automated safety. An unavailable allowance or unmet backend/host gate leaves the new mode opt-in for local scripted evaluation and the work explicitly not deployment-ready.
- [x] Run independent Spec/Standards code reviews using the requested `implement`/`code-review` workflow, fix actionable findings and repeat affected checks only. Audit changed browser/network artifacts for credentials; stage no database, vectors, model weights, `.env`, logs or private input files. Commit `Verify catalogue retrieval and document activation evidence` with the actual qualification status, not a fabricated completion claim.

## Self-review and handoff

Coverage: storage/import/rollback (1), shared commerce and freshness (2), read schema/bounds/unknowns (3), retrieval experiment and optional CPU backend (4), budgets and cancellation (5), natural interpretation/advice and safe Actions (6), real-browser/live/review gates (7). Every Review Focus case appears in the owning test task. Contract names and limits are shared above; no automatic spending or cloud action is hidden in a task.

Task test snippets pin representative observable assertions; each accompanying step names the additional cases and exact test files. Do not substitute a large set of shallow mocks for the shared HTTP/browser behavior. Keep the historical CAP-03 results unchanged and label all generated retrieval evaluation data honestly.

Owner approval was received and native implementation proceeded under `implement`, with independent Spec/Standards review. The plan does not authorize paid evaluation or default activation before the evidence gates pass.
