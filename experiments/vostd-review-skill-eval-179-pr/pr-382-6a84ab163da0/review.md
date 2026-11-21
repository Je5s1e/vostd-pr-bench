# Review: PR 382 snapshot `6a84ab163da0`

> Produced from the VOSTD coding-guideline criteria for maintainability, proof engineering, API contracts, and the two permitted workflow checks.
> Scope: `diff.patch` was authoritative, with `before/` and `after/` used only for surrounding context and line locations.

**Bottom line:** The split proof still depends on a placeholder axiom that can manufacture both a linear `PointsTo<MetaSlot>` token and unrelated facts about any aligned region slot. This is a blocking trust/soundness problem, not a completed removal of the former admits. In addition, the new absent-PTE law is exposed through a trait proof whose only implementation remains admitted; that small law should be proved from the executable PTE representation before merge.

## High

### `placeholder_slot_perm` manufactures ownership and arbitrary region facts

- **Guideline:** `centralize-trusted-boundaries`
- **Location:** `ostd/specs/mm/page_table/node/entry_owners.rs:104`
- **Evidence:** The changed axiom takes only a shared tracked borrow and requires only `regions.inv()`, address alignment, and an address bound, but returns a fresh linear permission and now ensures:

  ```rust
  pub axiom fn placeholder_slot_perm(paddr: Paddr, tracked regions: &MetaRegionOwners)
      -> (tracked res: PointsTo<MetaSlot>)
      requires regions.inv(), paddr % PAGE_SIZE == 0, paddr < MAX_PADDR,
      ensures
          res.is_init(),
          res.value().wf(regions.slot_owners[frame_to_index(paddr)]),
          regions.slot_owners[frame_to_index(paddr)].inner_perms.ref_count.value() != REF_COUNT_UNUSED,
          regions.slot_owners[frame_to_index(paddr)].path_if_in_pt is None;
  ```

  By contrast, `MetaRegionOwners::inv` only connects a real slot permission to its owner under `self.slots.contains_key(i)` (`ostd/specs/mm/frame/meta_region_owners.rs:64-75`); it does not state that every slot is non-`UNUSED` or has no page-table path. The caller then uses exactly the newly manufactured facts at `ostd/src/mm/page_table/node/entry.rs:780-821` to construct `child_owner` and discharge `Child::Frame(...).invariants(...)`.
- **Problem:** A shared borrow cannot transfer a unique `PointsTo` out of `regions`, and the preconditions do not imply the two asserted `slot_owners` facts. Repeated calls can also obtain multiple permissions for the same address, while a permission may still be present in `regions.slots`. Consequently, the axiom can establish the split invariant regardless of the actual allocator/metadata state, so the removed local admits have merely been replaced by a stronger global trust hole.
- **Suggestion:** Remove this placeholder axiom. During huge-page splitting, thread or split the real metadata-slot permissions through `MetaRegionOwners`, consuming/removing each permission from `regions.slots` (or use an existing ownership operation that does so), and derive `is_init`, `wf`, reference-count, and `path_if_in_pt` facts from that concrete ownership transition. If that ownership model is not implemented yet, keep the split path explicitly unverified rather than granting these facts for every aligned address.

## Medium

### The new absent-PTE law is supplied only by an admitted implementation

- **Guideline:** `complete-external-contracts`
- **Location:** `ostd/src/mm/page_table/mod.rs:338`
- **Evidence:** The patch strengthens `PageTableEntryTrait::new_properties` with:

  ```rust
  forall|level: PagingLevel|
      1 < level ==> !Self::new_absent_spec().is_last(level),
  ```

  This fact is used by `EntryOwner::absent_match_pte` (`ostd/specs/mm/page_table/node/entry_owners.rs:165-179`) and ultimately by the split proof. The only implementation remains:

  ```rust
  proof fn new_properties()
  {
      admit();
  }
  ```

  at `ostd/specs/arch/x86_64/page_table_entry.rs:315-318`. Nearby executable/spec definitions show `is_last(level)` is `level == 1 || HUGE-bit-is-set` (`:300-307`), so this particular new law should be derivable for the zero-valued absent PTE.
- **Problem:** Adding a postcondition to an already admitted proof expands the facts accepted on trust. The patch therefore relies on a newly trusted representation law even though the representation definition appears sufficient to prove it directly.
- **Suggestion:** Implement `new_properties` (or at least factor and prove the absent-PTE lemma from `new_absent_spec` and `is_last_spec`) so the newly added guarantee is checked against the actual PTE encoding. Keep any genuinely external facts at a narrowly documented boundary.

## Low

No evidence-backed low-severity findings.

## Evidence check record

- Read all 362 lines of the authoritative `diff.patch` and inspected the cited `before/` and `after/` contexts.
- Refutation check for the high finding: `MetaRegionOwners::inv` was inspected at `ostd/specs/mm/frame/meta_region_owners.rs:57-83`. Its permission initialization/well-formedness clauses are conditional on membership in `slots`, and it contains no general implication to non-`UNUSED` or `path_if_in_pt is None`; the axiom has no such membership precondition and performs no ownership removal.
- Refutation check for the medium finding: the sole `PageTableEntryTrait::new_properties` implementation in the snapshot was located and is an `admit()`. The claimed absent-entry law was compared with the adjacent `is_last` definition, indicating a direct proof should be possible rather than requiring a new trusted assumption.
- No changed `#[verifier::rlimit(...)]` was present, so the `rlimit > 200` workflow check was not triggered. No new or materially changed external specification for a `std`, `core`, or `alloc` API was present, so the upstream-reuse workflow check was not triggered.
- The strengthened `CursorMut::map` preconditions were checked against the lower-level page-table `map` contract; the new `item_not_mapped` and `item_slot_in_regions` obligations match requirements already imposed by that callee, so no API-precondition finding was retained.
- Per the fast-review instruction, no history inspection, Verus run, CI run, isolated caller experiment, or exhaustive checklist pass was performed. Findings are based on static evidence in the supplied patch and snapshots only.
