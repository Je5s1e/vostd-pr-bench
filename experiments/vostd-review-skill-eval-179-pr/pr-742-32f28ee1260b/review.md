# Review: PR 742 snapshot `32f28ee1260b`

> Produced from the authoritative `diff.patch`, with `before/` and `after/` used only for line-numbered context.  
> Scope: static fast review of the changes to `ostd/libs/id-alloc`, the new `vstd_extra::external::bitvec` trust bridge, and the accompanying proof-only edit. No history, Verus run, CI run, or caller experiment was performed.

**Bottom line:** The trusted `bitvec` model is centralized and guarded by an explicit model-validity predicate, and the patch adds no `rlimit` over 200. However, the verification port deletes two public APIs, removes a runtime misuse check on the mistaken premise that a Verus precondition replaces it, and leaves important public result paths without the guarantees promised by their documentation. These issues should be resolved before merge.

## High

None.

## Medium

### Preserve the runtime double-free check in `free_consecutive`

- **Guideline:** `preserve-exec-code`
- **Location:** `ostd/libs/id-alloc/src/lib.rs:488`
- **Quoted evidence:** The new comment says, `Drop .clone() (range unused after) and the in-loop debug_assert (already required).` The old body executed `debug_assert!(self.is_allocated(id));` for every element; the new loop only executes `self.bitset.set(id, false);`. The new formal requirement is `forall|i: int| ... ==> self@[i]` at lines 459–462.
- **Problem:** A Verus `requires` clause is erased and does not enforce the condition for ordinary Rust callers. Removing the `debug_assert!` therefore changes debug-build behavior from detecting a partially or wholly unallocated range to silently clearing it; the stated reason that it is “already required” conflates a proof obligation with a runtime check.
- **Suggestion:** Keep the original in-loop `debug_assert!(self.is_allocated(id))` and specify that call (or add the smallest faithful wrapper/spec needed to verify it). If executable behavior is intentionally being changed, make that an explicit API decision rather than a proof-driven rewrite.

### Do not silently remove the byte import/export API during verification

- **Guideline:** `preserve-exec-code`
- **Location:** `ostd/libs/id-alloc/src/lib.rs:311`
- **Quoted evidence:** The patch deletes the complete public definitions `pub fn from_bytes_with_capacity(slice: &[u8], capacity: usize) -> Self` (old lines 32–51) and `pub fn as_bytes(&self) -> &[u8]` (old lines 182–184); neither appears in the after tree.
- **Problem:** This is a caller-facing source-compatibility break embedded in a verification port. The patch gives no API rationale or migration path, and difficulty specifying `BitVec::from_slice`, `truncate`, or `as_raw_slice` is not evidence that consumers no longer need these operations.
- **Suggestion:** Restore both public operations and add faithful `bitvec` bridge contracts for the original callees. If removal is an intentional product/API change, separate and document it, including the replacement API or explicit compatibility decision.

### Specify why fallible allocation fails

- **Guideline:** `api-postconditions`
- **Location:** `ostd/libs/id-alloc/src/lib.rs:360`
- **Quoted evidence:** `alloc_consecutive` documents, `If allocation is not possible, it returns None`, but its `res is None` arm only states `final(self)@ == old(self)@` and `final(self).inv()` (lines 374–377). Likewise, `alloc_specific` documents, `If the ID is already allocated, it returns None, otherwise it returns the allocated ID`, while its `res is None` arm only preserves the state (lines 536–552).
- **Problem:** Verified callers cannot recover the documented reason for failure. In particular, `alloc_specific(id) == None` does not expose that `old(self)@[id]` was true, and `alloc_consecutive(count) == None` does not expose that `count == 0` or that no free run of the requested length exists. The success arms do not repair these missing failure-direction guarantees.
- **Suggestion:** Make each documented outcome bidirectional. For `alloc_specific`, return the exact option (or at least ensure `res is None <==> old(self)@[id]`) with the corresponding frame/update facts. For `alloc_consecutive`, define a reusable predicate for a free run and ensure that `None` means `count == 0` or no qualifying run exists, while retaining the unchanged-state guarantee.

### Give the derived `Clone` API a usable verified contract

- **Guideline:** `api-postconditions`
- **Location:** `ostd/libs/id-alloc/src/lib.rs:55`
- **Quoted evidence:** The verified public type keeps `#[derive(Clone)]` but adds `#[verifier::allow(autoderive_clone_without_spec)]`; its abstract view and invariant are defined immediately below as `bitvec_view(&self.bitset)` and `first_available_id == first_zero_seq(self@)`.
- **Problem:** `Clone` is part of the public executable API, but the suppression deliberately leaves it without a postcondition. A verified caller cannot establish that the clone has the same bitmap view or satisfies `inv()`, so it cannot naturally pass the result to the newly specified allocator operations.
- **Suggestion:** Provide a contract for cloning that ensures the result has the same view as `self` and preserves `inv()` when `self.inv()` holds, then remove `autoderive_clone_without_spec`. Use a specification mechanism for the existing derived implementation rather than rewriting runtime cloning solely for proof convenience.

## Low

None.

## Evidence check record

- Read all 1,230 lines of `diff.patch`; consulted the matching `before/` and `after/` files for complete function bodies and stable line numbers.
- Checked changed executable APIs, their contracts, the `IdAlloc` view/invariant, all newly introduced `assume_specification`, `uninterp`, `external_body`, and broadcast-axiom declarations, and the proof-only `embedding/mod.rs` hunk.
- The `bitvec` trust boundary is located under `verified_libs/vstd_extra/src/external/bitvec.rs`. Its generic contracts are guarded by `obeys_bitvec_model<T, O>()`, and unconditional model instances are restricted to primitive storage with `Lsb0`; no contradictory generic instance was found statically.
- No added or changed `#[verifier::rlimit(...)]` occurs in the authoritative patch, so there is no `rlimit > 200` finding.
- The external specifications target the third-party `bitvec` crate rather than `std`, `core`, or `alloc`; the narrow upstream-reusable-standard-spec workflow check was therefore not triggered.
- Static searches found no after-tree uses of the removed `IdAlloc::from_bytes_with_capacity` or `IdAlloc::as_bytes`; that does not eliminate the public API compatibility break for external consumers.
- **No-verification disclosure:** Per the fast-review constraint, I did not run Verus, compile/test the crate, inspect Git history, or construct isolated callers. Findings are based solely on quoted patch and snapshot evidence. The repository snapshot does not contain the authoritative `docs/coding-guidelines` pages; short names and criteria were taken from the supplied VOSTD review skill/personas.
