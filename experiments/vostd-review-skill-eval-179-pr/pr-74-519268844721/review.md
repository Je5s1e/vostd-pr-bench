# Review: `diff.patch` (`before` → `after`)

> Produced as a fast, non-exhaustive VOSTD review of the supplied snapshot.  
> Scope: `pr-74-519268844721/diff.patch`, checked against the corresponding files under `before/` and `after/`.

**Bottom line:** No high-severity issue was established. One medium-severity issue should be resolved before merge: the change removes the only modeled relationship between a `MetaSlotPerm` and the global metadata-slot array, while leaving the old clauses commented out and retaining the now-unconstrained `slot_idx` and unused `MetaSlotArray` model. This weakens the meaning of the well-formedness predicate used throughout the public lock-protocol contracts and leaves an evidently incomplete model transition.

## High

No findings.

## Medium

### The revised well-formedness predicate no longer proves membership in the metadata-slot array

- **Guidelines:** `canonical-spec-models`, `implement-inv-for-models`
- **Location:** `lock-protocol/src/exec/rw/mem_content/meta_slot/mod.rs:83`
- **Evidence:** The revised model still declares `pub slot_idx: nat`, but `MetaSlotPerm::wf` now contains the former membership conditions only as comments:

  ```rust
  pub tracked struct MetaSlotPerm {
      pub inner: PointsTo<MetaSlot>,
      pub slot_idx: nat,
  }

  pub open spec fn wf(&self) -> bool {
      //&&& 0 <= self.slot_idx < meta_slot_array.len()
      //&&& self.relate(meta_slot_array.vec[self.slot_idx as int])
      &&& self.inner.is_init()
      ...
  }
  ```

  Before the change, those were live conjuncts of `wf(&self, meta_slot_array: &MetaSlotArray)`. The patch also deletes `MemContent { meta_slot_array: MetaSlotArray }`, yet leaves `MetaSlotArray` defined at lines 121–137 with no remaining users. `PageTableNode::wf()` then relies on the weakened `self.perm@.wf()` at `lock-protocol/src/exec/rw/node/mod.rs:86–89`, and that predicate gates metadata dereferences and the lock API.
- **Problem:** A well-formed node no longer establishes that its permission names an in-bounds slot of the modeled global metadata array. The unconstrained `slot_idx`, the dead `MetaSlotArray`, and the commented-out invariant together make the new proof model strictly weaker and obscure whether global membership was intentionally replaced or merely bypassed to remove the `mem` parameter.
- **Suggestion:** Complete one coherent model transition. If global slot membership remains part of page-table validity, retain it through an owned/shared global-array token or another explicit relation that callers can carry without threading an ordinary `&MemContent` through every API. If it is intentionally no longer an invariant, remove `slot_idx`, `MetaSlotArray`, and the commented clauses, document the replacement ownership argument at the trusted `from_raw` boundary, and express the remaining intrinsic `MetaSlotPerm` validity through `Inv::inv()` rather than a standalone zero-argument `wf()`.

## Low

No findings.

## Evidence check record

- Read the supplied `diff.patch` and compared every listed `before/` and `after/` file; whitespace-insensitive comparison was used to separate the extensive formatting changes from semantic edits.
- Checked all changed files for `assume`, `admit`, `external_body`, and `rlimit`. Existing `assume(slot.invariants())` and trusted bodies were moved or reformatted, not newly introduced; no `#[verifier::rlimit(...)]` change or value above 200 was present.
- Traced all remaining references to `MemContent`, `MetaSlotArray`, `slot_idx`, and `meta_slot_array`. The after-snapshot has no consumer of `MetaSlotArray` and no live constraint on `slot_idx`.
- Examined changed public contracts and their immediate callers in `cursor.rs`, `node/{mod,child,entry}.rs`, `frame/mod.rs`, and `page_table.rs`. Apart from the removed global metadata relation, no separate strong API-precondition or API-postcondition defect was established from static evidence.
- No newly added or materially changed external specification for a `std`, `core`, or `alloc` API was present, so the upstream-spec reuse workflow check was not triggered.
- The requested fast override excluded history inspection, exhaustive rule-by-rule coverage, caller experiments, and Verus execution. Accordingly, **no verification was run**, and this report does not claim that the after-snapshot verifies or that the suggested redesign has been mechanically validated. The authoritative coding-guideline pages were not included in this review fixture; the cited rule identifiers and criteria come from the checked-in `vostd-code-review` skill.
