# Review: PR #505 isolated patch snapshot

> Fast, non-exhaustive VOSTD review of `diff.patch`, using the bundled `before/` and `after/` trees only for context.
> Scope: `pr-505-dffa7b932d72/diff.patch` (five changed heap files plus `ostd/src/mm/mod.rs`); no history analysis, child reviewers, Verus runs, or caller experiments were performed.

**Bottom line:** This patch should not merge as-is. It enables the heap module while disabling the global allocator registration and most of the slab/large-slot implementation, removes two runtime safety checks in ordinary builds, and introduces an inconsistent trusted `Repr` model. The remaining verified APIs also do not expose enough behavior for callers to reason about the free list.

## High

### The newly enabled heap module has its allocator and core public operations commented out

- **Guideline:** `preserve-exec-code`
- **Location:** `ostd/src/mm/mod.rs:21`, `ostd/src/mm/heap/mod.rs:119`, `ostd/src/mm/heap/slab.rs:176`, `ostd/src/mm/heap/slot.rs:113`
- **Evidence:** The patch changes `//pub mod heap;` to `pub mod heap;`, but the resulting module contains `/* #[alloc_error_handler] ... #[global_allocator] static HEAP_ALLOCATOR ... */`. It likewise wraps `impl Slab<SLOT_SIZE> { pub fn new ... pub fn dealloc ... }` and `HeapSlot::{alloc_large,dealloc_large}` in block comments. In the before snapshot all of these items are executable code (for example, `before/ostd/src/mm/heap/mod.rs:86-92`, `before/ostd/src/mm/heap/slab.rs:81-131`, and `before/ostd/src/mm/heap/slot.rs:80-125`).
- **Problem:** The change advertises and exports the heap module while deleting the mechanisms that install its allocator, construct/deallocate slabs, and allocate/deallocate large slots. Rustdoc in the surviving types still refers to these missing operations, so this is a functional/API regression rather than a proof-only refactoring.
- **Suggestion:** Restore the executable allocator handler/registration and the slab and large-slot implementations unchanged, then verify them incrementally. If the PR intentionally supports only a smaller heap subset, remove the misleading exports/docs and make that API reduction explicit rather than retaining dead code in comments.

### Verification gating removes safety enforcement from normal builds

- **Guideline:** `preserve-exec-code`
- **Location:** `ostd/src/mm/heap/slab.rs:109`, `ostd/src/mm/heap/slot_list.rs:89`
- **Evidence:** `SlabMeta::on_drop` now guards the outstanding-allocation panic with `#[cfg(feature = "allow_panic")]` (`after/ostd/src/mm/heap/slab.rs:109-114`), whereas it was unconditional at `before/ostd/src/mm/heap/slab.rs:47-51`. `SlabSlotList::push` similarly puts the former unconditional `const { assert!(SLOT_SIZE >= core::mem::size_of::<usize>()) };` behind `allow_panic` (`after/.../slot_list.rs:89-105`) and then unconditionally writes a pointer into the slot.
- **Problem:** In a build without `allow_panic`, dropping a slab with live slots silently proceeds, and an undersized `SLOT_SIZE` is no longer rejected before a pointer-sized write. The latter invalidates the immediately preceding safety justification and can write beyond the slot; these checks are invariants, not optional diagnostics.
- **Suggestion:** Keep the compile-time slot-size assertion unconditional and preserve the outstanding-allocation enforcement (using the project abort path if unwinding is disallowed). Model the required invariant for verification instead of compiling it out.

### The trusted `Repr` round-trip axiom contradicts its definitions

- **Guideline:** `complete-external-contracts`
- **Location:** `ostd/src/mm/heap/slab.rs:50`
- **Evidence:** `to_repr_spec(self, perm)` always returns `(MetaSlotSmall, perm)` (`:57-59`), while `from_repr_spec` always returns `SlabMeta { free_list: SlabSlotList::new_spec(), nr_allocated: 0 }` (`:65-67`). Nevertheless, `from_to_repr(self, perm)` is an empty `#[verifier::external_body]` proof (`:80-82`). The checked `Repr` trait contract requires this method to ensure `Self::from_repr_spec(self.to_repr_spec(perm).0, self.to_repr_spec(perm).1) == self` for arbitrary `self`.
- **Problem:** The admitted round trip therefore asserts that every `SlabMeta`, including one with a nonempty free list or nonzero `nr_allocated`, equals the fixed empty value. This is not an abstraction; it is a false trusted fact that can collapse reasoning about allocator state.
- **Suggestion:** Define a representation that actually carries the modeled `SlabMeta` state (and a `wf` predicate/permission tying it to storage), then prove the round-trip lemmas. Do not admit `from_to_repr` until the two conversion specifications are genuine inverses.

## Medium

### Free-list operations expose no caller-usable state or result contract

- **Guideline:** `api-postconditions`
- **Location:** `ostd/src/mm/heap/slot_list.rs:80`, `ostd/src/mm/heap/slot_list.rs:112`
- **Evidence:** The public `push(&mut self, slot: HeapSlot)` and `pop(&mut self) -> Option<HeapSlot>` declarations have no `requires` or `ensures` clauses. Yet their rustdoc promises front insertion/removal and `None` exactly for an empty list (`:72-80`, `:109-112`). The only list model added by the patch is the Boolean `is_empty_spec`, and `SlabMeta::alloc` specifies only the allocation counter, not the returned slot or free-list transition (`ostd/src/mm/heap/slab.rs:160-165`).
- **Problem:** A verified caller cannot obtain even the documented empty/nonempty transition, cannot connect a successful `pop` to the prior head, and cannot establish that a pushed slot is what a later pop returns. This leaves the allocator's ownership behavior outside the formal API despite bringing these methods under verification.
- **Suggestion:** Add an abstract sequence/set ownership model for the free list and specify `push` and `pop` against it, including both `Some` and `None` outcomes and final `self`. Strengthen `SlabMeta::alloc` to connect `Ok(slot)` to removal of that slot and preserve state on `Err`.

## Low

No low-severity findings.

## Evidence check record

- Treated `pr-505-dffa7b932d72/diff.patch` as authoritative and compared every cited change with the bundled before/after lines.
- Checked the `Repr` method contract statically: `from_to_repr` promises that `from_repr_spec` is a left inverse of `to_repr_spec`; the patch's constant conversions do not satisfy that equation for arbitrary `SlabMeta`.
- Found no added or changed `#[verifier::rlimit(...)]`; therefore there is no `rlimit > 200` finding.
- Searched the bundled after tree for duplicate local specifications of `Layout::{size,align}`, raw-pointer `read`/`write`, and `Option::map_or`; no evidence-backed spec-reuse finding was established in this limited snapshot.
- No Verus verification, compilation, tests, history inspection, exhaustive guideline sweep, or isolated caller experiment was performed. Findings are based solely on static patch and snapshot evidence.
