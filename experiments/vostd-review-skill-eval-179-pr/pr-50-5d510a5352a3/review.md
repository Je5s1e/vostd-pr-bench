# Review: PR 50 snapshot 5d510a5352a3

> Produced by a fast, non-exhaustive VOSTD review of the supplied immutable snapshot.
> Scope: `pr-50-5d510a5352a3/diff.patch` (409 lines), with the corresponding files under `before/` and `after/` used for context.

**Bottom line:** The `ensures`-to-`returns` migration is mostly contract-equivalent, but it weakens `PagingConstsTrait::NR_LEVELS` by deleting its caller-visible nonzero guarantee. That guarantee should be restored before merge so generic callers and implementations retain the original paging-level invariant.

## High

No high-severity findings.

## Medium

### Restore the nonzero guarantee on `NR_LEVELS`

- **Guideline:** `api-postconditions`
- **Location:** `lock-protocol/src/mm/page_table/mod.rs:294`
- **Evidence:** Before this change the trait method promised both `res == Self::NR_LEVELS_SPEC()` and `res != 0`. The new declaration is only:

  ```rust
  #[verifier::when_used_as_spec(NR_LEVELS_SPEC)]
  fn NR_LEVELS() -> PagingLevel
      returns
          Self::NR_LEVELS_SPEC(),
  ;
  ```

  `NR_LEVELS_SPEC` remains an unconstrained trait-level `spec fn`, so exact equality to it does not imply that it is nonzero. The concrete implementation returning `4` does not restore the property for callers reasoning through `PagingConstsTrait` or prevent another implementation from choosing zero.
- **Problem:** This is a real contract regression rather than a formatting-only conversion: callers lose the abstract fact that a paging system has at least one level, and the trait now admits an implementation excluded by the old contract.
- **Suggestion:** Keep the exact-result relationship while also preserving nonzeroness—for example, retain a named result with `ensures res == Self::NR_LEVELS_SPEC(), res != 0`, or add an equivalent trait-level invariant/contract that requires `Self::NR_LEVELS_SPEC() != 0` and is discharged by every implementation.

## Low

No low-severity findings.

## Evidence check record

- Read the complete supplied `diff.patch` and inspected the matching before/after context for every changed file.
- Compared the old and new `PagingConstsTrait` declarations and checked both in-snapshot implementations. Neither the abstract `NR_LEVELS_SPEC` declaration nor the surrounding trait adds a fact from which nonzeroness follows.
- The other changed exact-result contracts retain the same result equality through `returns`, or move the `when_used_as_spec`/contract obligation from an implementation to its trait declaration. No similarly strong caller-visible regression was found in this fast pass.
- The changed `external_body` implementations in `vstd_extra/src/bit_mapping.rs` remain governed by their trait-level exact-result contracts; the patch does not introduce a new trusted body or assumption there.
- No changed `#[verifier::rlimit(...)]` was present, and no value over 200 was found. No newly introduced standard-library external specification or strong duplicate-specification concern was identified in scope.
- **Verification disclosure:** Per the requested fast-review constraints, this review did not inspect repository history, run Verus or CI, execute caller experiments, delegate persona passes, or perform the skill's exhaustive rule checklist. Findings are based on static evidence in the supplied patch and before/after snapshots only.
