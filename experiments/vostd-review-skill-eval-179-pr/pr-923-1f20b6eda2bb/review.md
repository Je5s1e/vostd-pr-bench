# Review: PR 923 snapshot (`before` → `after`)

> Produced from `diff.patch` as the authoritative change, with the supplied `before/` and `after/` trees used only for context.
> Scope: `ostd/src/mm/heap/{mod.rs,slot.rs,slot_list.rs}` and `ostd/src/mm/mod.rs` as changed by `diff.patch`.

**Bottom line:** The verification work for the free-list itself is substantial, but this patch enables `mm::heap` only after commenting out the slab implementation, the global allocator bridge, and large-slot allocation/deallocation. That is a blocking executable/API regression, and the newly specified `push` operation also permits a no-panic path that irreversibly consumes an invalid slot. Restore the executable heap surface before merging, then retain the ghost ownership model around that unchanged runtime code.

## High

### The newly exported heap module removes its allocator implementation and most of its public API

- **Guideline:** `preserve-exec-code`
- **Location:** `ostd/src/mm/heap/mod.rs:3`
- **Evidence:** The patch changes `//pub mod heap;` to `pub mod heap;`, but the enabled module now contains `/*mod slab;*/`, comments out `slab::{Slab, SlabMeta}`, and encloses `GlobalHeapAllocator`, the `#[alloc_error_handler]`, `#[global_allocator] static HEAP_ALLOCATOR`, and the complete `GlobalAlloc for AllocDispatch` implementation in one block comment (`after/ostd/src/mm/heap/mod.rs:3-148`). It also comments out `HeapSlot::alloc_large`, `HeapSlot::dealloc_large`, and `LargeAllocFrameMeta` (`after/ostd/src/mm/heap/slot.rs:141-195,237-241`). The retained proc macro still generates `ostd::mm::heap::GlobalHeapAllocator` references (`after/ostd/libs/ostd-macros/src/lib.rs:144`), but that trait no longer exists in the compiled module.
- **Problem:** This is not a proof-only refactoring: the public module that the patch activates cannot provide the documented slab/global-allocation API, downstream uses of `#[global_heap_allocator]` expand against a missing trait, and the crate no longer registers the allocator dispatch shown by the original executable code. Large-slot construction and release disappear as well.
- **Suggestion:** Restore the original executable definitions and exports unchanged. Add contracts, ghost fields, or narrowly scoped verifier exclusions around unsupported pieces while preserving their Rust behavior; if the allocator/slab code is not ready to be enabled, keep `mm::heap` disabled rather than publishing a deliberately truncated replacement.

## Medium

### `push` can consume a non-slab slot without returning it

- **Guideline:** `api-preconditions`
- **Location:** `ostd/src/mm/heap/slot_list.rs:136`
- **Evidence:** The new precondition is conditional: `cfg!(feature = "allow_panic") ==> slot.slot_info() is SlabSlot` (`after/ostd/src/mm/heap/slot_list.rs:137-145`). In a build without `allow_panic`, the non-slab arm executes `return` (`after/ostd/src/mm/heap/slot_list.rs:160-165`). The function takes `slot: HeapSlot` by value and returns `()`, while its postcondition merely says the list remains unchanged for that arm (`after/ostd/src/mm/heap/slot_list.rs:146-153`). `HeapSlot` owns the exclusive `PointsToRaw` permission introduced at `after/ostd/src/mm/heap/slot.rs:36-37`.
- **Problem:** A legal verified call in the no-panic configuration can pass `SlotInfo::LargeSlot`; the call then consumes the only abstract owner of the memory, inserts nothing, and offers no result through which the caller can recover it. This also conflicts with the rustdoc statement that invalid slot kinds panic.
- **Suggestion:** For the current unit-returning API, require `slot.slot_info() is SlabSlot` unconditionally (and keep the size/alignment obligations under that valid case). If rejecting non-slab slots is intended runtime behavior, change the API to return the rejected `HeapSlot` in an error/result and specify that ownership-preserving outcome.

## Low

| Finding | Guideline | Detail |
|---|---|---|
| The verifier trust boundary on the thread-safety impls is not disclosed (`ostd/src/mm/heap/slot_list.rs:41-53`). | `document-verified-apis` | Both `unsafe impl Sync` and `unsafe impl Send` are newly marked `#[verifier::external]`. The adjacent safety comment argues the Rust aliasing discipline but does not tell reviewers that these unsafe impls are assumed rather than verified. Add one concise trust-boundary statement identifying exactly what remains externally justified. |

## Evidence check record

- Read all 585 lines of `diff.patch`; treated it as the immutable, authoritative review input.
- Compared each changed hunk with the corresponding files under `before/` and `after/`, and searched the `after/` tree for allocator registrations and callers of the removed heap API.
- Confirmed that the only visible `#[global_allocator]`, allocation-error handler, and `GlobalHeapAllocator` definition are inside the new block comment, while the exported proc macro still names `ostd::mm::heap::GlobalHeapAllocator`.
- Checked the `HeapSlot` ownership invariant and the complete `SlabSlotList::push` contract/body to confirm the no-panic non-slab path consumes the by-value slot and leaves the list unchanged.
- No `#[verifier::rlimit(...)]` change appears in the patch, and no new or materially changed external specification for a `std`, `core`, or `alloc` API appears in scope.
- Per the requested fast-review limits, no Git history, exhaustive rule enumeration, sub-agent pass, Verus run, build, or isolated caller experiment was performed. Findings are therefore based on static patch and before/after evidence only; verification status was not independently checked.
