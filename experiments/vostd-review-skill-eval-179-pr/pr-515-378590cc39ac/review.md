# Review: PR #515 isolated diff snapshot

> Fast, non-exhaustive VOSTD review of `diff.patch`, with `before/` and `after/` used only for surrounding context. No history review, Verus run, build, test, or caller experiment was performed.
>
> Scope: `ostd/src/mm/frame/mod.rs`, `ostd/src/mm/frame/unique.rs`, and `ostd/src/sync/rcu/mod.rs` as changed by the supplied 205-line patch.

**Bottom line:** The RCU constructor change should be fixed before merge. It removes the only const-capable empty `RcuOption` constructor even though the module's example and an in-tree test still require it, and it simultaneously moves the invariant-establishing inner constructor out of the explicitly verified impl. No rlimit over 200, new external `std`/`core`/`alloc` specification, or duplicated specification was introduced in this patch.

## High

None.

## Medium

### Restore the const empty constructor without silently widening the trust boundary

- **Guidelines:** `preserve-exec-code`, `centralize-trusted-boundaries`
- **Location:** `ostd/src/sync/rcu/mod.rs:235` and the deletion after `ostd/src/sync/rcu/mod.rs:787`
- **Evidence:** The patch removes `#[verus_verify]` from the impl containing `const fn new_none() -> (res: Self)` while retaining its strong `ensures res.is_nullable(), res.wf()`. It also deletes:

  ```rust
  pub const fn new_none() -> Self {
      Self(RcuInner::new_none())
  }
  ```

  The after-tree still documents `static RCU: RcuOption<Box<usize>> = RcuOption::new_none();` at `ostd/src/sync/rcu/mod.rs:151`, and the `#[cfg(ktest)]` caller at `ostd/src/sync/rcu/non_null/either.rs:565` still executes `RcuOption::new_none()`. The remaining `RcuOption::new(Option<P>)` at lines 779-787 is not `const`, so it cannot replace the deleted API in the documented static initialization use case.
- **Problem:** This is not a proof-neutral refactoring: it removes the caller-facing const API, leaves its documented and test callers stale, and changes the proof status of the private constructor whose postcondition establishes the empty RCU invariant. The patch provides no explicit trusted-boundary marker or explanation for relying on that postcondition after removing the verification marker.
- **Suggestion:** Restore `RcuOption::new_none()` as a public const constructor. Keep the invariant-establishing path verified; if the active Verus toolchain cannot verify the const form, split the const runtime initializer from a verified constructor/wrapper, make any unavoidable external boundary explicit, and document the concrete tool limitation and follow-up rather than silently removing `#[verus_verify]`.

## Low

None.

## Evidence check record

- Read the complete supplied `diff.patch` and the relevant before/after contexts around all three hunks.
- Confirmed statically that the after-tree has no `pub const fn RcuOption::new_none`, while both the rustdoc example and the `ktest` caller still name it.
- Confirmed statically that `RcuOption::new` is a non-const `pub fn`, so it does not preserve the documented static-initialization capability.
- Confirmed the patch contains no `#[verifier::rlimit(...)]` change and no new or materially changed external specification for a `std`, `core`, or `alloc` API.
- No Verus verification, compilation, tests, history analysis, or isolated caller experiment was run, per the fast-review override. Consequently, the report does not claim a reproduced diagnostic; it reports the directly visible API and verification-boundary regression.
