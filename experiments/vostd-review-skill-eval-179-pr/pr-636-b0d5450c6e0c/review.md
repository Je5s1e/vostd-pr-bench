# Review: PR #636 snapshot b0d5450c6e0c

> Produced from the supplied `diff.patch`, with the matching `before/` and `after/` trees used only for surrounding context.
> Scope: the 71-line patch changing `ostd/specs/mm/page_table/cursor/va_lemmas.rs`, `ostd/specs/mm/page_table/node/entry_owners.rs`, and `ostd/src/mm/kspace/kvirt_area.rs`.

**Bottom line:** No strong evidence-backed maintainability, proof/trust, assumption, API-contract, invariant, rlimit, or specification-reuse defect was found in the supplied patch. The central change is favorable: it replaces `EntryOwner::new_untracked_frame`, a trusted axiom, with a checked proof constructor whose strengthened preconditions are the facts needed by `EntryOwner::inv_base`; the sole caller is updated consistently. No merge-blocking or pre-merge correction is recommended from static review.

## High

None.

## Medium

None.

## Low

None.

## Evidence check record

- Read `diff.patch` in full and compared each hunk with its `before/` and `after/` source context.
- Trust boundary: `ostd/specs/mm/page_table/node/entry_owners.rs:268-297` changes an axiom into a proof function with a concrete `EntryOwner` construction. The patch removes rather than adds a trusted assumption.
- Invariant/contract check: the added requirements at `entry_owners.rs:277-281` correspond to the frame branch of `EntryOwner::inv_base` at `entry_owners.rs:849-869` (valid leaf level, safe/aligned physical range, and `C::raw_item_well_formed`) plus the advertised untracked result (`!C::tracked(...)`). The constructor's fields definitionally support its remaining postconditions and `Child::Frame(...).wf(res)`.
- Caller check: `ostd/src/mm/kspace/kvirt_area.rs:961-1021` retains the `collect_largest_pages` bounds, page-size alignment, physical-address progression, and end bound needed for the stronger constructor contract; `MappedItem::Untracked` and `KernelPtConfig`'s raw-item model supply the untracked/configuration obligations.
- Proof-maintenance check: the new `assert(inc.va.inv())` at `ostd/specs/mm/page_table/cursor/va_lemmas.rs:190` states the exact validity premise subsequently required by `AbstractVaddr::align_down_concrete`; the enclosing preconditions include the no-wrap bound used to preserve the incremented index invariant.
- API check: the new proof constructor pins every returned component and exposes the invariant and `Child::wf` relation needed by its only caller. No unsupported weakening or caller-visible omission was found.
- Workflow checks: the patch adds or changes no `#[verifier::rlimit(...)]`, and it introduces no external specification for a `std`, `core`, or `alloc` API.
- Specification-reuse check: no new mathematical model or overlapping external specification is introduced. The constructor reuses `C::raw_item_well_formed`, `C::tracked`, `C::item_from_raw_spec`, `EntryOwner::inv_base`, and `Child::wf` rather than creating parallel predicates.
- **No-verification disclosure:** Per the requested fast-review override, no Verus run, standalone experiment, CI run, history inspection, or exhaustive guideline checklist was performed. Conclusions are static and limited to the supplied patch and snapshot context.
