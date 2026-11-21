# Review: PR 632 isolated patch

> Scope: `pr-632-1be8099780ff/diff.patch` was the authoritative input, with the supplied `before/` and `after/` trees used only for surrounding context.

**Bottom line:** No strong evidence-backed maintainability, proof/trust, assumption, API-contract, or invariant defect was found in the patch. The change replaces several axiomatic constructors and state transitions with proof bodies while preserving their stated results. The one new precondition on `CursorContinuation::tracked_restore` is supported by the existing caller invariant, and the patch introduces no `rlimit` change or new external specification for a `std`, `core`, or `alloc` API.

## High

None.

## Medium

None.

## Low

None.

## Evidence check record

- Read all 239 lines of `diff.patch` and inspected the affected definitions and direct callers in both supplied trees.
- Checked the new `tracked_restore` contract at `ostd/specs/mm/page_table/cursor/owners.rs:154`: its added requirement is `old(self).idx < old(self).children.len()`. The direct changed-context caller is reached from `tracked_pop_level_owner`, which requires `old(self).inv()`; `CursorContinuation::inv` establishes `children.len() == NR_ENTRIES` and `0 <= idx < NR_ENTRIES` at lines 307–310, so the new requirement does not expose an unsupported caller assumption.
- Checked the constructors added to `verified_libs/vstd_extra/src/ghost_tree.rs`: `tracked_new` returns exactly `Self::new(value, level, children)`, and `tracked_into_parts` exposes exactly the existing `value()` and `children()` projections. Neither claims `inv()` for arbitrary inputs.
- Checked the replacements in `meta_region_owners.rs`: mint inserts the same slot into `frame_obligations` and returns an obligation for that slot; redeem has the existing positive-count precondition and removes that slot. Their bodies match the pre-existing state-transition specifications.
- Checked the replacement `tracked_cursor_entry_new`: direct construction establishes every field equality in its unchanged postcondition.
- Searched the authoritative patch for `#[verifier::rlimit(...)]`, new `assume`, and newly added axioms. No rlimit or assumption was added; the axiom occurrences are removals.
- No reusable `std`, `core`, or `alloc` external specification was added or materially changed.
- No Verus build, CI verification, standalone proof experiment, repository history inspection, or exhaustive guideline checklist was performed, per the requested fast-review override. Conclusions are therefore static-review conclusions over the supplied snapshot, not independent verification results.
