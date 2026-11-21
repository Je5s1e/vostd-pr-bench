# Review: PR 485 snapshot `6fac7bc837f6`

> Fast, non-exhaustive VOSTD review of `diff.patch`, using the captured `before/` and `after/` trees for context.
> Scope: the 35 paths changed by `pr-485-6fac7bc837f6/diff.patch`; no repository history, sub-agent passes, Verus execution, caller experiments, or exhaustive guideline enumeration was performed.

**Bottom line:** The new segment-ID freshness axiom is stated for every mathematical map, including maps whose domain already contains every integer, so it admits a false proposition into the trusted proof environment and should block the change until its finite-domain premise is made explicit and proved. Separately, five newly added `rlimit(8000)` annotations exceed VOSTD's workflow cap of 200 by 40× and should be decomposed before merge.

## High

### The fresh-segment-ID axiom is false for unrestricted maps

- **Guideline:** `centralize-trusted-boundaries`
- **Location:** `ostd/specs/mm/embedding/mod.rs:4187`
- **Quoted evidence:**

  ```rust
  pub type SegmentId = int;

  pub open spec fn fresh_segment_id(m: Map<SegmentId, SegmentEntry>) -> SegmentId {
      choose|id: SegmentId| !m.dom().contains(id)
  }

  pub axiom fn axiom_fresh_segment_id_not_in_dom(m: Map<SegmentId, SegmentEntry>)
      ensures
          !m.dom().contains(fresh_segment_id(m)),
  ;
  ```

  The new axiom has no `requires m.dom().finite()` (or any other non-total-domain condition), yet it quantifies over arbitrary `Map<int, SegmentEntry>` values. For a map whose domain is all integers, no integer satisfies the `choose` predicate and the axiom's postcondition is false. Because this is an axiom, that bad instantiation makes the proof environment inconsistent rather than merely making a caller hard to verify. The axiom is used immediately at `ostd/specs/mm/embedding/mod.rs:2772`, `:3241`, and `:3245` to justify insertion of supposedly fresh entries.

  **Suggestion:** Make finiteness part of `VmStore`'s segment-map invariant and replace this axiom with a proved lemma requiring `m.dom().finite()` (or use a monotonically allocated ghost identifier whose freshness follows from the store invariant). Do not leave a universally quantified freshness fact as a trusted axiom.

## Medium

### Five new proof limits exceed the project cap by 40×

- **Guideline:** `decompose-before-raising-rlimit`
- **Locations:** `ostd/specs/mm/frame/linked_list/linked_list_owners.rs:491`, `:645`; `ostd/src/mm/frame/linked_list.rs:834`, `:1158`, `:1541`
- **Quoted evidence:** each location newly adds `#[verifier::rlimit(8000)]`; the VOSTD workflow rule caps changed rlimits at `200`.

  These annotations are attached respectively to the new list-rewiring proofs `pop_preserves_relate_region` and `insert_preserves_relate_region`, and to `CursorMut::take_current`, `CursorMut::insert_before`, and `LinkedList::drop`. A value of 8000 is 40 times the permitted cap and makes verification cost and solver fragility part of the API implementation.

  **Suggestion:** Split the quantified list-rewiring and region-preservation arguments into smaller helper lemmas, keeping every resulting `rlimit` at or below 200.

## Low

No low-severity findings were retained in this fast pass.

## Evidence check record

- Read the complete captured `diff.patch` scope structurally and inspected the relevant `before/` and `after/` source around the retained findings.
- Confirmed that `SegmentId` is `int`, that `axiom_fresh_segment_id_not_in_dom` has no finiteness precondition, and that its three new call sites rely on the unconditional postcondition.
- Confirmed from the patch that all five `rlimit(8000)` annotations listed above are additions. Other visible rlimits were not reported unless changed in this diff.
- Attempted to refute the freshness finding statically: arbitrary Verus `Map` domains are not constrained to be finite by the displayed signature, so an all-integer domain remains a legal counterexample to the axiom as written.
- No Verus verification, build, tests, isolated caller experiments, history analysis, or exhaustive rule coverage was performed, per the requested fast-review constraints. CI/verification status was not independently checked.
