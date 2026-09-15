# 13 — Handle mobile controls and interaction traps

**What to build:** Keep approved Shopping Tasks working through mobile layouts, custom controls, delayed content, repeated labels, accessibility requirements, and browser speech input.

**Blocked by:** 07 — Deliver bilingual constraint-based discovery; 08 — Locate cart and order-history destinations; 11 — Undo Reversible Mutations.

**Status:** ready-for-agent

- [ ] Mobile menu and filter-drawer controls expose usable semantics and execute correctly.
- [ ] Custom dropdowns, dialogs, size swatches, mini-cart state, and infinite content work through the same Action contract.
- [ ] Delayed rendering and disabled controls do not produce premature or invalid Actions.
- [ ] Repeated labels carry enough semantic context to target the intended product or order.
- [ ] The Panel supports complete keyboard operation, visible focus, semantic controls, announced status, RTL, and non-color-only state.
- [ ] Stop remains reachable during every responsive and modal state.
- [ ] Browser speech input receives a documented Arabic and English manual smoke test without entering the deterministic reasoning gate.
- [ ] Browser Evaluation Cases cover representative desktop and mobile trap combinations.
