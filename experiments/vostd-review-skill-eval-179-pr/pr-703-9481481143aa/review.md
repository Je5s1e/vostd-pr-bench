# Review: PR 703 snapshot `9481481143aa`

> Fast, non-exhaustive VOSTD review using `diff.patch` as the authoritative change and the supplied `before/` and `after/` trees for surrounding context.
> Scope: the 179-line patch changing `Cargo.lock`, `ostd/src/util/mod.rs`, and `ostd/src/util/range_alloc.rs`.

**Bottom line:** The newly trusted allocator contracts are false for a sequence of calls permitted by the safe public API. Because the model records only the immutable full range and `free` has no contract, an arbitrary out-of-range free block can later be returned successfully even though both allocation contracts promise that every successful result lies within the full range. This proof-soundness issue should block merge until allocator state and its preservation rules are modeled.

## High

### An unconstrained `free` can falsify both trusted allocation contracts

- **Guidelines:** `complete-external-contracts`, `implement-inv-for-models`, `api-preconditions`, `api-postconditions`
- **Locations:** `ostd/src/util/range_alloc.rs:23`, `ostd/src/util/range_alloc.rs:68`, `ostd/src/util/range_alloc.rs:118`, `ostd/src/util/range_alloc.rs:157`
- **Quoted evidence:** The new model contains only the immutable endpoints:

  ```rust
  pub ghost struct RangeAllocatorModel {
      pub ghost start: int,
      pub ghost end: int,
  }
  ```

  Both allocation methods are trusted with `#[verifier::external_body]`; `alloc_specific` promises on success that

  ```rust
  self@.start <= allocate_range.start
      && allocate_range.end <= self@.end
  ```

  and `alloc` similarly promises that its returned range is within `self@`. However, the newly trusted `free` has no `requires` or `ensures` at all:

  ```rust
  #[verifier::external_body]
  pub fn free(&self, range: Range<usize>) {
      ...
      freelist.insert(free_range.start, FreeRange::new(free_range.clone()));
  }
  ```

- **Problem:** For `RangeAllocator::new(0..10)`, `alloc_specific(&(0..10))` initializes and empties the freelist. The safe call `free(20..21)` then inserts the out-of-range block, and `alloc_specific(&(20..21))` returns `Ok(())`; equivalently, `alloc(1)` returns `20..21`. These concrete successful executions contradict the trusted bounds postconditions. The same missing state model also leaves the contracts unable to express the allocator's essential availability, non-overlap, allocation, and reclamation transitions.
- **Suggestion:** Extend `RangeAllocatorModel` with abstract allocation/free state and an invariant tying every freelist block to the managed range, ordering, and non-overlap. Give `free` a precondition (or an ownership token) proving that the nonempty range is in-bounds and currently allocated, and specify its state transition; specify successful allocation as removing an available range while preserving the invariant. Then verify the bodies, or keep only a narrowly documented trusted boundary whose complete contracts are proved consistent with the executable behavior.

## Medium

No findings.

## Low

No findings.

## Evidence check record

- Read all 179 lines of `diff.patch` and compared the complete before/after versions of `ostd/src/util/range_alloc.rs`; inspected the natural `IoMemAllocator` callers and their ownership documentation.
- Refutation check: after allocating the entire initial `0..10` free block, the freelist is empty; `free(20..21)` inserts exactly `20..21`; the next allocation therefore succeeds from that sole block. The `free` signature is safe and imposes no formal range or ownership obligation, so no contract excludes this witness.
- Consolidated the absent allocator invariant, unconstrained `free`, and incomplete allocation state transitions because they share one root cause and one correction.
- The patch changes no `#[verifier::rlimit(...)]`, so no limit exceeds 200. It adds no external specification for a `std`, `core`, or `alloc` API, and the fast static scan found no evidence-backed specification-reuse issue.
- The fixture does not include `docs/coding-guidelines/{README,maintainability,proof-engineering,workflow}.md`; the named findings are grounded in the bundled VOSTD review skill/persona criteria and quoted source evidence. No exhaustive rule-by-rule pass was attempted.
- **No-verification disclosure:** Per the requested fast-review override, no Verus or CI run, history analysis, caller experiment, controlled variant, or other dynamic verification was performed. Conclusions are based on static inspection of the captured patch and context only.
