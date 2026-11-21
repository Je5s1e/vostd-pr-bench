# Review: PR 440 snapshot `0ba029a82c8d` (`diff.patch`)

> Fast, non-exhaustive review against the VOSTD maintainability, proof-engineering,
> workflow, and API-contract criteria requested for this snapshot.
> Scope: the two files and 191-line patch captured in `diff.patch`, with the supplied
> `before/` and `after/` trees used for local context.

**Bottom line:** No strong evidence-backed high-, medium-, or useful low-severity issue was found in the scoped patch. The changes preserve the existing contracts and executable behavior while replacing private iterator fields with the public `IntoIter` specification model and explicitly re-establishing `AbstractVaddr::inv()`. The patch adds no trust primitive, external specification, API contract change, or `rlimit` change.

## High

None.

## Medium

None.

## Low

None.

## Evidence check record

- Read all of `diff.patch` and inspected the corresponding before/after context around `CursorOwner::do_inc_index`, `KVirtArea::map_frames`, and `KVirtArea::map_untracked_frames`.
- At `ostd/specs/mm/page_table/cursor/owners.rs:850-862`, the added proof spells out the four existing clauses of `AbstractVaddr::inv()` after updating one in-domain index; it neither weakens the invariant nor introduces an assumption.
- At `ostd/src/mm/kspace/kvirt_area.rs:541-569` and `801-945`, every former `it.elements`/`it.pos` reference is replaced consistently by `vec::into_iter_elts(it.snapshot@)`/`it.index()`. The loop contracts, trigger-bearing indexed facts, current-element bridge, and prefix-sum bounds retain their before-patch structure.
- Static scan of added lines found no `assume`, `admit`, `axiom fn`, `external_body`, external specification, or `#[verifier::rlimit(...)]`. Consequently there is no newly enlarged trust boundary, no changed `std`/`core`/`alloc` external spec to propose upstream, and no changed rlimit above the workflow cap of 200.
- The patch applies cleanly to the supplied `before/` tree under `git apply --check`.
- Per the requested fast-review override, no repository history, exhaustive rule enumeration, caller experiment, Verus run, or other verification command was performed. Conclusions are static and limited to the supplied snapshot.
