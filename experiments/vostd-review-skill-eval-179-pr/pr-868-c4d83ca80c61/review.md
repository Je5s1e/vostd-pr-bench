# Review: PR 868 snapshot

> Scope: `diff.patch` is the authoritative change set; `before/` and `after/` were used only for immediate source context. Fast isolated review of maintainability, proof/trust boundaries, assumptions, API contracts, invariants, rlimit values above 200, and specification reuse.

**Bottom line:** No strong, evidence-backed review finding was identified. The patch adds a focused bridge from `relate_region` to `LinkedListOwner::inv`, exposes the resulting invariant and region well-formedness in the `push_front`/`push_back` contracts, and records mutable-reference alias preservation needed by the back-insertion call chain. The sole visible rlimit is an unchanged value of 200, not a newly introduced or over-cap value.

## High

No findings.

## Medium

No findings.

## Low

| Finding | Guideline | Detail |
|---|---|---|
| None | — | No useful low-severity issue was supported by the reviewed evidence. |

## Evidence check record

- **Invariant bridge:** `ostd/specs/mm/frame/linked_list/linked_list_owners.rs:245-253` defines `LinkedListOwner::inv` as the list-id condition, permission-vector lengths, and per-index `inv_at`. `relate_region` supplies the same shape conditions and a per-index `relate_region_at` (`:319-335`), while `relate_region_at` includes both clauses of `inv_at` (`:315-316`). The added lemma at `:350-362` therefore matches the existing predicate definitions and centralizes a reusable implication rather than duplicating caller proofs.
- **Push contracts:** `ostd/src/mm/frame/linked_list.rs:257-280` and `:352-379` add `wf_region` and owner-invariant postconditions to `push_front` and `push_back`. Their bodies recover the post-insertion owner, invoke the new bridge lemma, and retain the established region relation; the `push_back` path also explicitly establishes `self.wf_region`.
- **Alias-preservation contracts:** `ostd/src/mm/frame/linked_list.rs:642-650` states that the returned ghost cursor's list is the same mutable list at return and final states. `insert_before` propagates that relationship at `:1197-1200`, supporting the `push_back` receiver after mutation without adding a trust annotation or assumption.
- **`pop_front` rewrite:** `ostd/src/mm/frame/linked_list.rs:303-308` merely groups the two existing `Some`-case guarantees under one implication; no precondition or promised result is removed.
- **Trust and assumptions:** The patch adds no `external_body`, `assume`, `admit`, or other trust-boundary escape. The nearby pre-existing `lazy_get_id` assumption is outside the changed hunks.
- **Rlimit:** The authoritative patch contains no added, removed, or changed `#[verifier::rlimit(...)]`. The surrounding `insert_before` remains at exactly 200 (`ostd/src/mm/frame/linked_list.rs:1186-1188`), so there is no value above the requested cap.
- **Specification reuse:** The new `lemma_relate_region_implies_inv` is a local, reusable proof lemma over project-specific linked-list ownership predicates. No new external specification for `std`, `core`, or `alloc` is introduced.
- **Verification disclosure:** Per the fast-review instruction, no Verus run, build, tests, history inspection, exhaustive guideline pass, or isolated caller experiment was performed. Conclusions are static and limited to `diff.patch` plus the supplied before/after context.
