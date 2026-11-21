# Review: PR 505 snapshot cb2be5a80af1

> Produced from the supplied `diff.patch`, its `before/` and `after/` snapshots, and the VOSTD review criteria.
> Scope: `pr-505-cb2be5a80af1/diff.patch` (8 changed paths); no commit metadata was supplied.

**Bottom line:** This snapshot is not merge-ready. The new `Repr<MetaSlotSmall>` implementation admits round-trip laws for a representation that discards all `SlabMeta` state, which makes the proof model inconsistent. The patch also removes core heap APIs by commenting them out and disables two executable safety checks when `allow_panic` is off.

## High

### The admitted representation round trip equates every slab state with an empty slab

- **Guideline:** `complete-external-contracts`
- **Location:** `ostd/src/mm/heap/slab.rs:57`
- **Evidence:** `to_repr_spec` returns only `(MetaSlotSmall, perm)` for every `self`, while `from_repr_spec` always returns `SlabMeta { free_list: SlabSlotList::new_spec(), nr_allocated: 0 }` (lines 57–70). Nevertheless, `from_to_repr(self, perm)` and `to_from_repr(r, perm)` are accepted with `#[verifier::external_body]` (lines 73–86). The `Repr` trait's round-trip contract requires `from_repr_spec(to_repr_spec(self, perm)) == self`.
- **Problem:** The representation loses both `free_list` and `nr_allocated`, so the admitted round-trip law is false for any non-empty or allocated slab. In particular, it lets proofs rewrite an arbitrary `SlabMeta` to one whose allocation count is zero, invalidating reasoning about the exact safety condition checked by `on_drop`.
- **Suggestion:** Do not admit these round-trip proofs. Give `MetaSlotSmall` (and its tracked permission) a faithful model of the slab fields and prove both laws, or keep `SlabMeta` out of the generic `Repr`/linked-list model until such a representation exists.

### Required heap functionality is removed by block comments

- **Guideline:** `preserve-exec-code`
- **Locations:** `ostd/src/mm/heap/mod.rs:104`, `ostd/src/mm/heap/slab.rs:176`, `ostd/src/mm/heap/slot.rs:113`
- **Evidence:** The patch wraps the allocation error handler and `#[global_allocator] static HEAP_ALLOCATOR` in `/* ... */`; it likewise comments out the entire `impl Slab` containing `new` and `dealloc`, and `HeapSlot::alloc_large`/`dealloc_large`. At the same time, `ostd/src/mm/mod.rs` changes `//pub mod heap;` to `pub mod heap;`.
- **Problem:** Verification scaffolding has deleted the executable entry points that construct and reclaim both slab and large heap slots and has stopped installing the allocator dispatch. This is a caller-visible functional regression, not a proof-only refactor; the remaining rustdoc even links to methods that no longer exist.
- **Suggestion:** Restore the original executable items unchanged and verify/specify them incrementally. If a body cannot yet be verified, isolate that body behind a narrowly documented temporary trust boundary rather than commenting the API and allocator registration out.

### `allow_panic = false` now bypasses memory-safety invariants

- **Guideline:** `preserve-exec-code`
- **Locations:** `ostd/src/mm/heap/slab.rs:109`, `ostd/src/mm/heap/slot_list.rs:89`
- **Evidence:** `SlabMeta::on_drop` previously always panicked when `nr_allocated != 0`; the new code guards the only terminating action with `#[cfg(feature = "allow_panic")]` (lines 109–114), so the no-panic build returns and permits the backing frame to be dropped with outstanding slots. In `SlabSlotList::push`, the formerly unconditional `const { assert!(SLOT_SIZE >= size_of::<usize>()) }` is also now guarded by `allow_panic` (lines 89–105), immediately before writing a pointer-sized value into a slot under the comment that this size condition holds.
- **Problem:** Disabling panic support must not turn failed safety checks into successful execution. The first change can reclaim storage still referenced by allocated slots; the second permits a pointer-sized write without preserving the slot-size premise that justifies it.
- **Suggestion:** Preserve these checks in every feature configuration. Use the project's non-unwinding abort path for `not(feature = "allow_panic")`, and keep the const generic size assertion unconditional (or enforce the same bound at construction/type level).

## Medium

### Trusted standard-library specifications are declared beside one caller

- **Guideline:** `centralize-trusted-boundaries`
- **Location:** `ostd/src/mm/heap/slot_list.rs:11`
- **Evidence:** `slot_list.rs` locally introduces `assume_specification` declarations for `<*mut T>::write`, `<*mut T>::read`, and `Option::map_or` (lines 11–19). The patch separately creates `verified_libs/vstd_extra/src/external/alloc_types.rs` specifically as a shared external-specification module.
- **Problem:** These generic `core` trust declarations are repository-wide models, not properties of `SlabSlotList`. Keeping them next to this caller makes later users likely to add competing declarations and prevents one audit point for their exact signatures and contracts.
- **Suggestion:** Move the raw-pointer and `Option::map_or` specifications into the appropriate `vstd_extra::external` modules (or reuse the vendored/upstream model if one exists), then import them here. Audit the generic bounds and behavioral contracts once at that central boundary.

## Low

No low-severity findings.

## Evidence check record

- Read the complete supplied 663-line patch and inspected the cited `before/` and `after/` source around every finding.
- Checked the `Repr` trait contract in the available repository snapshots: `from_to_repr` promises that decoding the encoded representation returns the original `self`; this directly contradicts the new constant encoding/decoding pair.
- Confirmed `allow_panic` is an optional feature and that the cited no-panic branches therefore exist; the safety actions have no fallback in those branches.
- Searched the supplied `after/` tree for callers and duplicate declarations. No `#[verifier::rlimit(...)]` change appears in the patch, so the `> 200` workflow check is not triggered.
- The new `core::alloc` external specifications are upstream-reusable in principle; this fast review records the concrete local-placement issue but did not inspect upstream Verus history.
- Per the requested fast-review override, no Verus run, build, tests, isolated caller experiment, git-history audit, or exhaustive guideline pass was performed. Findings are based on static before/after evidence only.
