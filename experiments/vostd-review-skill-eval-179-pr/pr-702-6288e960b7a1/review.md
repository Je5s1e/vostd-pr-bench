# Review: PR 702 snapshot (`diff.patch`)

> Produced from the VOSTD coding-guideline categories and the skill's API-contract criteria.
> Scope: authoritative `diff.patch`, with `before/` and `after/` used only for surrounding context; changed files are `ostd/src/sync/mod.rs`, `ostd/src/sync/spin.rs`, and `ostd/src/sync/wait.rs`.

**Bottom line:** The new ghost-state design substantially strengthens the relationship between `WaitQueue::num_wakers` and the protected queue, but the relationship still rests on an in-line `assume` for counter overflow. Because `enqueue` has no corresponding input limit or runtime overflow handling, the verified exact-count invariant and the lock-free `is_empty` result are not established for every documented call. This is a blocking trust/API-contract issue; no other strong finding was identified in the fast static review.

## High

### The exact queue/count invariant relies on an unchecked overflow assumption

- **Guidelines:** `centralize-trusted-boundaries`, `api-preconditions`
- **Location:** `ostd/src/sync/wait.rs:254-272`
- **Evidence:** `enqueue` is a public safe API with no precondition and first executes `wakers.push_back(waker)`. Its atomic update then contains:

  ```rust
  self.num_wakers => fetch_add(1);
  update prev -> next;
  ghost count_auth => {
      count_auth.agree(&count_mirror);
      assert(prev == count_mirror@);
      assume(prev < u32::MAX);
      count_auth.update(&mut count_mirror, next);
  }
  ```

  The PR also changes `WaitQueue::wf` to require `g@ == v as int` and `WakersPredicate::inv` to require `mirror@ == wakers@.len()`. Thus the assumed inequality is now the step that excludes `AtomicU32::fetch_add` wrapping while the queue length continues to grow.
- **Problem:** A caller can repeatedly invoke the documented `enqueue(&self, waker)` API; neither its contract nor its executable body prevents the counter from reaching `u32::MAX`. On the next call, `fetch_add` wraps to zero while `push_back` has increased the queue length, so the new exact-count invariant cannot be justified without the `assume`; at runtime, the lock-free `is_empty` check can then report an empty queue even though entries remain. Keeping this fact as a local assumption also expands the trusted proof surface precisely where the PR is intended to replace assumptions with linked ghost state.
- **Suggestion:** Define an executable overflow policy and verify it instead of assuming the bound. For example, make enqueueing fallible or otherwise reject/cap the operation before mutating the queue when the representable count is exhausted, then derive `prev < u32::MAX` from that checked branch. If the project can prove a stronger representation/resource bound that makes overflow unreachable, expose that fact through a centralized reviewed specification and use it here; do not retain a caller-local `assume`.

## Medium

None.

## Low

None.

## Evidence check record

- Read all 869 lines of the authoritative patch and inspected the corresponding `before/` and `after/` source around every changed hunk.
- Confirmed that the pre-change `assume(prev < u32::MAX)` existed only under a trivial atomic ghost invariant; the patch materially changes its role by using it to maintain the newly introduced exact authoritative/mirror/queue-length relationship.
- Checked the changed public contracts for `new_with_pred`, `lock`, `try_lock`, `take_predicate_state`, `put_predicate_state`, and manual `drop`; no additional high-confidence contract defect was found statically.
- No `#[verifier::rlimit(...)]` change appears in the patch, so the `> 200` workflow check is not triggered. No new or materially changed external specification of a `std`, `core`, or `alloc` API appears in scope.
- Per the requested fast-review override, this review used no subagents, history inspection, exhaustive rule enumeration, Verus execution, or isolated caller experiments. Consequently, verification/build status and solver acceptance were not independently checked; conclusions are based on static diff and snapshot evidence only.
