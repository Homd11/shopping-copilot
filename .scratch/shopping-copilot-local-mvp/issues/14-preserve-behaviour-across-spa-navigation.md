# 14 — Preserve behaviour across SPA navigation

**What to build:** Preserve the approved Shopping Task contract across client-side routes, controlled inputs, optimistic updates, loading states, event-stream reconnect, and duplicate delivery.

**Blocked by:** 06 — Resume a Shopping Task after refresh; 13 — Handle mobile controls and interaction traps.

**Status:** ready-for-agent

- [ ] Category, cart, and account routes have SPA variants at the same shopper-facing destinations.
- [ ] One variant keeps filter state only in components and another mirrors it to the URL for measured comparison.
- [ ] Client-side history changes and settled DOM state trigger a fresh Snapshot without relying on full page load.
- [ ] Controlled inputs receive verified values and optimistic updates settle before success is reported.
- [ ] Skeleton and delayed-content states wait for meaningful interactive content.
- [ ] A direct URL fast path falls back to visible controls when component state does not change as expected.
- [ ] Event-stream reconnect resumes from the last event without repeating an Action or losing pending task state.
- [ ] SPA versions pass the applicable safety, refresh, Undo, Confirmation, and navigation regressions.
