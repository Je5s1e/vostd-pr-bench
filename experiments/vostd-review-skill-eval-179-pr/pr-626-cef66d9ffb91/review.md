# Review: `diff.patch` (captured before/after trees)

> Produced from the VOSTD coding-guideline criteria and the skill's API-contract criteria.
> Scope: fast, non-exhaustive inspection of `pr-626-cef66d9ffb91/diff.patch`, with the captured `before/` and `after/` trees used only for surrounding context.

**Bottom line:** The new retry loop relies on a trusted `external_body` contract that says a failed traversal restores all tracked state exactly, but the implementation can update `cursor_own` before a later stray-node check returns `None`. That mismatch can inject a false equality into verification and should block merging until the failure contract or implementation is made faithful.

## High

### A failed traversal is specified as transactional although the body does not roll back

- **Guideline:** `complete-external-contracts`
- **Location:** `ostd/src/mm/page_table/cursor/locking.rs:283`
- **Quoted evidence:** The new trusted contract states:

  ```rust
  r is None ==> {
      &&& *final(cursor_own) == *old(cursor_own)
      &&& *final(regions) == *old(regions)
      &&& *final(guards) == *old(guards)
  },
  ```

  Yet the same `#[verifier::external_body]` function descends by mutating its tracked cursor model before all later failure points:

  ```rust
  let tracked child_cont = cont.tracked_make_cont(next_idx, new_guard);
  cursor_own.continuations.tracked_insert(cursor_own.level - 1, cont);
  cursor_own.continuations.tracked_insert(cursor_own.level - 2, child_cont);
  cursor_own.level = (cursor_own.level - 1) as PagingLevel;
  ```

  and subsequently has failure exits at lines 433-434 and 508-509:

  ```rust
  if is_stray {
      return None;
  }
  ```

- **Problem:** A legal execution can descend through one or more present child nodes, thereby lowering `cursor_own.level` and adding continuations, and then observe a deeper node as stray and return `None`. There is no rollback before either `return None`, so the exact-state equality used by the new loop invariant at lines 142-148 is not justified by the external body. Because this is a trusted contract, the issue is a proof-soundness gap rather than merely a missing proof.
- **Suggestion:** Make the trusted contract match the failure behavior. Prefer restructuring traversal so tentative descent does not commit changes to the caller's `cursor_own`, `regions`, and `guards` until a non-stray root is obtained. If failed attempts can allocate or otherwise change ownership state, replace the equality postcondition with precise preservation/extension properties that describe those effects, and rewrite the retry invariant to consume those properties. Do not retain the full rollback claim unless every `None` path explicitly reconstructs the old tracked state and accounts for resources created during the attempt.

## Medium

No findings.

## Low

No findings.

## Evidence check record

- Read the complete patch and inspected the corresponding captured before/after definitions of `lock_range`, `try_traverse_and_lock_subtree_root`, `get_kernel_page_table`, `relates_owner`, and the changed cursor call sites.
- Traced the new `None` postcondition into the retry invariant and checked every `return None` in the helper against earlier mutations of `cursor_own`.
- Checked the patch for changed `#[verifier::rlimit(...)]` attributes; none were introduced or changed, so the `rlimit > 200` workflow check was not triggered.
- No new or materially changed external specification for a `std`, `core`, or `alloc` API was present, so the upstream-spec workflow check was not triggered.
- No Verus run, caller experiment, repository history inspection, or exhaustive rule-by-rule verification was performed, per the requested fast-review constraints. Findings are based on static evidence from `diff.patch` and the captured source context only.
