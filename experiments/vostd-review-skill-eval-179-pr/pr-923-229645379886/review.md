# Review: PR 923 snapshot `diff.patch`

> Produced from the supplied patch and its `before/` and `after/` source snapshots, using the VOSTD maintainability, proof/trust, and API-contract criteria requested for this fast review.
> Scope: all 590 lines of `diff.patch`; changed code in `ostd/src/mm/heap/{mod.rs,slot.rs,slot_list.rs}` and `ostd/src/mm/mod.rs`, with adjacent and repository-wide caller context from the supplied snapshots.

**Bottom line:** I found no evidence-backed high- or medium-severity defect in this non-exhaustive review. The new ownership model and `push`/`pop` contracts account for the list order, node permissions, address uniqueness, alignment, and the feature-dependent rejection path. One low-severity import-preservation issue remains; no `rlimit` over 200 or new reusable external specification for a `std`, `core`, or `alloc` API appears in the patch.

## High

None.

## Medium

None.

## Low

| Finding | Guideline | Detail |
|---|---|---|
| Preserve the inherited `core` import tree | `preserve-exec-code` | `ostd/src/mm/heap/slot.rs:3-16` changes the original `use core::{alloc::AllocError, ptr::NonNull};` into the new flat line `use core::ptr::NonNull;`, while other temporarily unavailable inherited imports are commented in place. The guideline specifically requires retaining the original import statement and commenting individual unused entries. Keep its original shape, for example `use core::{/* alloc::AllocError, */ ptr::NonNull};`, so later re-enabling the disabled large-slot implementation remains a localized edit. |

## Evidence check record

- Read the supplied `diff.patch` in full and compared every changed file against the corresponding `before/` and `after/` files.
- Traced all supplied-snapshot references to `HeapSlot`, `SlabSlotList`, `Slab`, `SlabMeta`, `AllocDispatch`, `LargeAllocFrameMeta`, and `HeapSlot::new`. This confirmed that the slab, large-slot allocator, and global allocator code remain deliberately outside the enabled dependency closure, rather than being silently replaced by the verified list implementation.
- Checked the new `HeapSlot` invariant and constructor contract against the list invariant and the `push`/`pop` postconditions. The tracked raw range is split into the link word plus remainder on push and joined on pop; address freshness is derived from exclusive header permissions; the model records LIFO order; and the returned slot restores the same address, size class, range, and provenance.
- Checked `paddr_to_vaddr` in the supplied `after/` context. Its dual specification models addition of `LINEAR_MAPPING_BASE_VADDR`, matching `HeapSlot::paddr` under the new linear-mapping bounds.
- Searched the patch for `rlimit`, `admit`, `assume`, `external_body`, and external specifications. There is no `rlimit`, `admit`, `assume`, or `external_body`; the only trust annotations are the two `#[verifier::external]` marker-trait implementations for `Send` and `Sync`, each adjacent to the existing exclusivity rationale. No changed `std`, `core`, or `alloc` external specification was found.
- No Verus run, Rust build, test, caller experiment, history inspection, or exhaustive guideline checklist was performed, per the fast-review constraints. Conclusions are static and limited to the supplied snapshot.
