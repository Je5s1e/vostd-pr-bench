# Review: PR #403 snapshot `a1f2685897f4`

> Produced from the supplied `diff.patch` and before/after trees, using the VOSTD maintainability, proof-engineering, API-contract, and limited workflow criteria.
> Scope: fast isolated review of `pr-403-a1f2685897f4/diff.patch`; no Git history, Verus run, exhaustive rule pass, or caller experiment was performed.

**Bottom line:** No high-severity issue was found. The patch removes an axiom-dependent use in the linked-list code, but it replaces the old trusted helpers with two new public `external_body` proof helpers that have no callers and are unnecessary given the direct tracked-field borrow used by this same change. Those helpers should be removed before merge so the refactor actually eliminates this avoidable trust surface.

## High

None.

## Medium

### Remove the unused trusted mutable-borrow helpers

- **Guideline:** `centralize-trusted-boundaries`, `reuse-existing-specifications`
- **Location:** `vstd_extra/src/cast_ptr.rs:257`
- **Evidence:** The patch adds:

  ```rust
  #[verifier::external_body]
  pub proof fn borrow_mut_inner_perms(tracked &mut self) -> (tracked result: &mut T::Perm)
  ```

  and, at `vstd_extra/src/cast_ptr.rs:269`:

  ```rust
  #[verifier::external_body]
  pub proof fn borrow_mut_points_to(tracked &mut self) -> (tracked result: &mut simple_pptr::PointsTo<R>)
  ```

  A repository-wide search of the supplied after-tree finds only these definitions, with no call to either helper. Meanwhile the changed caller at `ostd/src/mm/frame/linked_list.rs:972` directly borrows the tracked field:

  ```rust
  slot.in_list.store(Tracked(&mut frame_own.meta_perm.inner_perms.in_list), list_id);
  ```

- **Problem:** Both public helpers ask Verus to trust their contracts despite having no consumer, while the patch itself shows that ordinary tracked-field borrowing suffices for the motivating operation. Keeping unused `external_body` APIs needlessly retains a proof trust boundary and exposes contracts that future proofs could rely on without verification.
- **Suggestion:** Delete both `borrow_mut_inner_perms` and `borrow_mut_points_to`. If a future concrete caller cannot express a required borrow directly, add the narrowest helper at that time and isolate/document the tool limitation at the trusted boundary.

## Low

None.

## Evidence check record

- Read the authoritative 476-line `diff.patch` in full and inspected relevant before/after context for every changed Verus file.
- Searched both supplied trees for `take_inner_perms`, `put_inner_perms`, `take_points_to`, `borrow_mut_inner_perms`, and `borrow_mut_points_to`. The two new borrow helpers have no callers in the after-tree; the removed `PointsTo::take_inner_perms`/`put_inner_perms` pair had served the now-rewritten linked-list call site.
- Inspected the new `ReprPtr`/`PointsTo` address derivation and conversion contracts. The changed contracts consistently derive the address from the underlying `PPtr`/permission; no evidence-backed API precondition or postcondition defect was found in this fast pass.
- No `#[verifier::rlimit(...)]` change and no new or materially changed external specification for a `std`, `core`, or `alloc` API appears in the supplied diff, so neither limited workflow check was triggered.
- **No-verification disclosure:** Per the requested fast-review constraints, this review did not run Verus, CI, history analysis, exhaustive guideline enumeration, or isolated client experiments. Findings are based on static diff and supplied-tree evidence only.
