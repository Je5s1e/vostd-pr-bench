# Review: `diff.patch` (fast isolated snapshot)

> Produced from the VOSTD coding-guideline review criteria and the skill's API-contract criteria.
> Scope: the changes captured in `diff.patch`, with static before/after context from `before/` and `after/`.

**Bottom line:** The patch usefully replaces several trusted page-table facts with per-configuration proofs, but two contract changes should be fixed before merge. The newly specified external offset helper has no valid-level precondition even though its executable arithmetic underflows at level zero, and the end-range proof rewrites an intentionally wrapping shift by imposing a stronger trait obligation that excludes the full-width boundary the old implementation supported.

## High

None.

## Medium

### Constrain the trusted offset helper to valid paging levels

- **Guideline:** `complete-external-contracts`, `api-preconditions`
- **Location:** `ostd/src/mm/page_table/mod.rs:1169`
- **Evidence:** The patch adds an exact contract to a trusted body but no precondition:

  ```rust
  #[verifier::external_body]
  fn pte_index_bit_offset<C: PagingConstsTrait>(level: PagingLevel) -> (ret: usize)
      ensures
          ret as int == pte_index_bit_offset_spec::<C>(level),
  {
      C::BASE_PAGE_SIZE().ilog2() as usize
          + nr_pte_index_bits::<C>() * (level as usize - 1)
  }
  ```

  `PagingLevel` is `u8`, so `level == 0` is admitted by the signature while `level as usize - 1` underflows (and can panic when overflow checks are enabled). The surrounding paging APIs consistently treat levels as one-based; for example, `PageTableConfig::item_into_raw` promises `1 <= res.1 <= NR_LEVELS` at `ostd/src/mm/page_table/mod.rs:296`.
- **Problem:** `external_body` makes the new postcondition trusted for every value admitted by the signature, but the body is not a total, non-panicking implementation for `level == 0`. The contract therefore omits a real execution precondition at the trust boundary.
- **Suggestion:** Add `requires 1 <= level <= C::NR_LEVELS()` (or the narrowest actual valid-level bound), prove that it prevents subtraction/multiplication overflow, and discharge that requirement at every caller. If zero is intended to be supported, change the executable operation and specification together so its behavior is explicit rather than relying on build-profile overflow behavior.

### Preserve the intentional full-width wrapping case instead of excluding it

- **Guideline:** `preserve-exec-code`, `api-preconditions`
- **Location:** `ostd/src/mm/page_table/mod.rs:209`
- **Evidence:** The new required trait proof includes:

  ```rust
  (Self::TOP_LEVEL_INDEX_RANGE_spec().end as int) * (pow2(
      pte_index_bit_offset_spec::<Self::C>(Self::C::NR_LEVELS()) as nat,
  ) as int) <= usize::MAX as int,
  ```

  and `pt_va_range_end` now executes an ordinary shift:

  ```rust
  let shifted = idx_end << offset;
  let ret = shifted.wrapping_sub(1);
  ```

  The before snapshot deliberately used

  ```rust
  C::TOP_LEVEL_INDEX_RANGE().end.unbounded_shl(
      pte_index_bit_offset::<C>(C::NR_LEVELS()) as u32,
  ).wrapping_sub(1)
  ```

  and documented the boundary where `idx.end * 2^offset == 2^64`, yielding `usize::MAX` after the wrapping subtraction (`before/ostd/src/mm/page_table/mod.rs:794`). The existing range constraint only required the product to be at most `2^ADDRESS_WIDTH`, with `ADDRESS_WIDTH <= 64`; equality at `2^64` was therefore intentional.
- **Problem:** The new `<= usize::MAX` obligation is not merely a proof of the former API invariant: it rules out the supported equality-at-`2^64` configuration so that the rewritten executable expression is easy to verify. This unnecessarily narrows implementations of `PageTableConfig` and loses the full-width behavior explicitly handled by the old code.
- **Suggestion:** Keep the original `unbounded_shl(...).wrapping_sub(1)` executable form and prove its modulo semantics, allowing the pre-subtraction product to be `<= 2^64`. If the project intentionally no longer supports full-width configurations, make that API restriction explicit in the trait documentation and justify the observable executable rewrite; otherwise do not encode it as a new implementor obligation.

## Low

| Finding | Guideline | Detail |
|---|---|---|
| Replace speculative trust comments with concrete status | `document-real-proof-debt` | `ostd/src/mm/page_table/mod.rs:224`, `:230`, `:241`, and `:260` add `// dubious: why is this an axiom` above required trait proof methods. These methods are discharged by each implementation rather than declared as `axiom fn`, so the comments blur the trust boundary and give no actionable limitation. Remove them, or replace them with a specific TODO that identifies the remaining trusted fact, why it cannot yet be derived, and the intended follow-up. |

## Evidence check record

- Read all 604 lines of `diff.patch` and inspected the corresponding before/after context for every changed file.
- Searched the patch for `external_body`, `axiom`, `assume`, `admit`, proof contracts, and `rlimit`. No added or changed `#[verifier::rlimit(...)]` was present, so there is no `rlimit > 200` finding. No new or materially changed external specification for a `std`, `core`, or `alloc` API was present.
- Checked all visible `PageTableConfig` implementations and the one-based paging-level contracts around the changed helpers. Dormant plain-Rust/test implementations already diverge from the verified trait surface in the snapshot and were not treated as patch-introduced findings.
- The trust surface is reduced overall: the patch removes two free axioms and three `external_body` annotations from the range calculation, replacing them with proof obligations on concrete configurations.
- No Verus run, compilation, history inspection, exhaustive rule pass, or caller experiment was performed, as required by this fast isolated review. Findings are based on static patch and snapshot evidence only.
