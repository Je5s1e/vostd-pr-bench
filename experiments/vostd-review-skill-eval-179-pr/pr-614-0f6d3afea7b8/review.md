# Review: PR 614 snapshot (`diff.patch`)

> Produced from the VOSTD maintainability, proof-engineering, workflow, and API-contract review criteria.
> Scope: the complete supplied `diff.patch` (18 files, 398 insertions and 251 deletions), with corresponding `before/` and `after/` source used for local context. This was a fast, non-exhaustive review.

**Bottom line:** No strong evidence-backed high-, medium-, or useful low-severity issue was found in the supplied change. The patch materially reduces the trusted surface by replacing several axioms and one uninterpreted state transformer with checked proof functions and explicit postconditions. The added invariant and API preconditions have matching facts at the changed callers in the inspected context; no changed `rlimit` annotation or newly introduced assumption was found.

## High

None.

## Medium

None.

## Low

None.

## Evidence check record

- **Scope and context:** Read all 1,345 lines of `diff.patch` and inspected the affected definitions and callers in `before/` and `after/`. Primary areas checked were tracked-resource construction, cursor invariants and VA mutation, metadata-slot usage, node-owner updates, executable-code preservation, and public proof contracts.
- **Trust boundary:** The patch removes axiomatic versions of `tracked_cursor_mut_at_owner`, `tracked_front_owner`, `never_drop_restores_nodes_locked`, `do_zero_below_level`, `tracked_set_va_in_node`, `tracked_new_frame`, and `active_entry_not_in_free_pool`. It also removes `set_children_perm` plus its `#[verifier::external_body]` axiom and replaces the abstract update with explicit field and permission postconditions (`ostd/src/mm/page_table/node/mod.rs:525`). No added `assume`, `admit`, `external_body`, uninterpreted function, or axiom was present in added diff lines.
- **Tracked constructors:** The former `FrameEntry`, `SegmentEntry`, `UniqueEntry`, linked-list cursor-owner, and frame-entry-owner axioms are replaced by direct tracked construction. Changed callers consume or obtain the required tracked resources, including `LinkedListOwner::tracked_take` before `tracked_front_owner` (`ostd/src/mm/frame/linked_list.rs:222`).
- **API contracts and invariants:** The new `tracked_set_va_in_node` requirements explicitly capture zero offset, canonical-half agreement, locked-range membership, and `level <= guard_level` (`ostd/specs/mm/page_table/cursor/va_lemmas.rs:418`); the changed jump caller establishes the leading-bit relationship before invoking it (`ostd/src/mm/page_table/cursor/mod.rs:1575`). The strengthened cursor invariant ties continuation indices above the guard level to the prefix (`ostd/specs/mm/page_table/cursor/owners.rs:678`), and the new helper derives the matching indices from the locked range (`ostd/specs/mm/page_table/cursor/va_lemmas.rs:371`). Static inspection did not establish an unnecessary caller obligation or a missing output guarantee.
- **Metadata-slot invariant:** `item_slot_in_regions` and frame-entry metaregion soundness now exclude `PageUsage::PageTable` (`ostd/specs/mm/page_table/cursor/cursor_fn_specs.rs:159`, `ostd/specs/mm/page_table/node/entry_owners.rs:613`). The changed map/remove paths propagate that fact before mutating `paths_in_pt` (`ostd/src/mm/page_table/cursor/mod.rs:3154`, `ostd/src/mm/page_table/cursor/mod.rs:3618`). No contradiction with the inspected node-owner invariant was found.
- **Proof structure and reuse:** The added VA lemmas have concrete current callers, and local searches found no demonstrated equivalent helper whose signature and conditions would safely replace them. The constructor proofs reuse direct tracked struct construction rather than adding new trusted models.
- **Workflow checks:** The only `#[verifier::rlimit(infinity)]` occurrence visible in the patch is unchanged context, not an added or modified annotation. No new or materially changed external specification for a `std`, `core`, or `alloc` API appears in scope.
- **No-verification disclosure:** Per the requested fast-review override, no Verus run, isolated caller experiment, history analysis, or exhaustive rule-by-rule pass was performed. Conclusions are based only on static patch and before/after context, so successful verification and CI remain review preconditions.
