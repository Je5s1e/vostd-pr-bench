# Review: PR 699 captured patch `6f1ed3a06cce`

> Fast, non-exhaustive VOSTD review of `diff.patch`, with the captured `before/` and `after/` trees used only for local context.
> Scope: `pr-699-6f1ed3a06cce/diff.patch` (168 lines), changing `ostd/src/util/range_alloc.rs` and `verified_libs/vstd_extra/src/trans_macros.rs`.

**Bottom line:** The allocator is not yet verified end to end: `alloc` derives its safety and result facts from a new local `assume` because the lock carries no freelist invariant. The public contracts also exclude a documented fallible call shape and make every `free` caller supply panic permission, while an executable rewrite loses the original panic diagnostic. The trusted assumption is blocking; the contract and executable-shape issues should also be corrected before merge.

## High

### The verified allocator still trusts its central state invariant

- **Guidelines:** `centralize-trusted-boundaries`, `api-postconditions`
- **Location:** `ostd/src/util/range_alloc.rs:140`
- **Evidence:** The loop proof contains:

  ```rust
  // `alloc` currently has no callers. Trust that any future caller preserves the
  // allocator's intended freelist invariant until the lock carries this predicate.
  assume(self@.start <= value.block.start
      && value.block.start <= value.block.end
      && value.block.end <= self@.end);
  ```

  Yet `RangeAllocator::view` at lines 28-34 exposes only `fullrange`, and `alloc`'s postcondition at lines 119-125 states only conditional size/bounds facts. It neither models nor preserves freelist availability or non-overlap.
- **Problem:** These assumed bounds justify the executable subtraction at line 147 and the returned-range bounds at lines 132-134. The fact is an invariant of allocator state, not an obligation a future caller can preserve through the current public abstraction; placing it inside `alloc` leaves the main correctness premise trusted and gives callers no state-transition guarantee from which allocation exclusivity can be established.
- **Suggestion:** Define an allocator/freelist invariant (including ordered, in-range, non-overlapping free blocks), attach it to the protected lock state, and prove that initialization, `alloc_specific`, `alloc`, and `free` preserve it. Remove the local `assume`, and extend the allocator model/contracts with the availability transition needed to prove that successful allocations are disjoint.

## Medium

### `alloc_specific` requires containment instead of returning `Err`

- **Guideline:** `api-preconditions`
- **Location:** `ostd/src/util/range_alloc.rs:65`
- **Evidence:** The patch adds:

  ```rust
  self@.start <= allocate_range.start,
  allocate_range.end <= self@.end,
  ```

  The natural caller `ostd/src/io/io_mem/allocator.rs:21-27` documents that an unavailable range returns `None`, then converts `alloc_specific(&range).ok()?`. Its selector at lines 119-131 rejects only non-overlap, so a partially overlapping request can reach `alloc_specific`; the implementation can safely report `Err` because it chooses a target only when a free block contains the request (lines 85-92).
- **Problem:** The new preconditions exclude a documented fallible input and encode the success domain as a caller obligation. A future verification of `IoMemAllocator::acquire` cannot establish containment from `find_allocator`'s overlap check, even though the runtime API already has `Result`/`Option` failure behavior for this case.
- **Suggestion:** Remove the two containment preconditions. Keep non-panicking arithmetic justified by local checks/invariants, and specify success and failure in terms of whether the requested nonempty range is available within the allocator.

### `free` unconditionally requires panic permission

- **Guidelines:** `complete-external-contracts`, `api-preconditions`
- **Location:** `ostd/src/util/range_alloc.rs:176`
- **Evidence:** The new contract requires bare `may_panic()` at line 183, although the rustdoc says the function panics only when the freelist has not been initialized (lines 171-175). The adjacent TODO explicitly proposes the intended conditional form: ``self@.freelist is None ==> may_panic()``.
- **Problem:** Every caller must currently provide panic permission, including the natural initialized path `IoMemAllocator::recycle` at `ostd/src/io/io_mem/allocator.rs:41-46`, where allocation/acquisition has already initialized the freelist. This is stronger than the documented panic condition and results from the missing state model rather than a genuine restriction on all calls.
- **Suggestion:** Model freelist initialization and require `may_panic()` only when the modeled state is uninitialized (or expose a non-panicking initialized-state precondition). Preserve the documented conditional panic behavior instead of requiring unconditional permission.

### The proof-oriented unwrap rewrite changes the panic diagnostic

- **Guideline:** `preserve-exec-code`
- **Location:** `ostd/src/util/range_alloc.rs:187`
- **Evidence:** The before image used:

  ```rust
  let freelist = lock_guard.as_mut().unwrap_or_else(|| {
      panic!("Free a 'KVirtArea' when 'VirtAddrAllocator' has not been initialized.")
  });
  ```

  The patch comments out that executable form and replaces it with `lock_guard.as_mut().unwrap_or_panic()` at line 189. No concrete obstacle or equivalence argument is recorded, and the application-specific panic message is no longer passed to the replacement.
- **Problem:** This is not merely a proof annotation: it changes observable failure diagnostics and leaves the original implementation as commented-out code. The maintainability rule requires preserving executable shape or documenting the concrete Verus obstacle after first specifying the original callee.
- **Suggestion:** Specify the original `unwrap_or_else`/panic path and restore the original executable code. If the active toolchain cannot verify it, record that concrete limitation and use the smallest behavior-preserving wrapper that retains the original message, rather than leaving the old body commented out.

## Low

No evidence-backed low-severity findings in this fast pass.

## Evidence check record

- Read `diff.patch` in full and compared both changed files against their captured `before/` and `after/` versions.
- Read local caller context in `ostd/src/io/io_mem/allocator.rs`, including `acquire`, `recycle`, and `find_allocator`.
- Static trust/workflow scan found one added `assume`, no changed `#[verifier::rlimit(...)]`, and no newly defined or materially changed external specification for a `std`, `core`, or `alloc` API.
- The fixture does not contain `docs/coding-guidelines/{README,maintainability,proof-engineering,workflow}.md`; findings were therefore grounded in the bundled VOSTD review skill/persona criteria and quoted source evidence. This fast review did not attempt an exhaustive rule-by-rule compliance audit.
- **No-verification disclosure:** Per the requested fast-review scope, no Verus run, CI run, history inspection, caller experiment, controlled variant, or other dynamic verification was performed. Findings are based on static patch and nearby captured-context evidence only.
