# Review: PR #518 snapshot `4cb9ee7caa9e`

> Produced from the supplied `diff.patch` with `before/` and `after/` used only for static context.
> Scope: the authoritative patch changes `ostd/src/mm/frame/mod.rs`, `ostd/src/mm/frame/unique.rs`, and `ostd/src/sync/rcu/mod.rs`.

**Bottom line:** The RCU constructor move is blocking. It removes `RcuOption::new_none()` even though an in-tree test still calls it, and introduces the same null constructor on `Rcu`, whose non-optional read API unconditionally unwraps the loaded pointer. Restore the constructor to `RcuOption` and retain the non-null invariant on `Rcu`.

## High

### The nullable constructor was moved onto the non-null RCU type

- **Guidelines:** `preserve-exec-code`, `implement-inv-for-models`
- **Location:** `ostd/src/sync/rcu/mod.rs:730`
- **Quoted evidence:** The patch adds `impl<P: NonNullPtr + Send> Rcu<P> { ... pub const fn new_none() -> Self { Self(RcuInner::new_none()) } }`, deletes the identical method from `impl ... RcuOption<P>`, and weakens `Rcu<P>::type_inv` by deleting `&&& !self.0.is_nullable()`. The resulting tree still contains `let rcu: RcuOption<Either32> = RcuOption::new_none();` at `ostd/src/sync/rcu/non_null/either.rs:565`. Moreover, `Rcu::read` returns `RcuReadGuard`, whose `get` implementation is `self.0.get().unwrap()` at `ostd/src/sync/rcu/mod.rs:847`.
- **Problem:** This is both an immediate API break for the existing `RcuOption::new_none()` caller and a violation of the abstraction boundary between nullable `RcuOption` and non-null `Rcu`. If the new `Rcu::new_none()` is used, `Rcu::read().get()` reaches an unconditional unwrap with a null pointer, while the patch has removed exactly the type invariant that previously excluded this state.
- **Suggestion:** Keep `new_none()` on `RcuOption<P>`, remove it from `Rcu<P>`, and restore `&&& !self.0.is_nullable()` in `Rcu<P>::type_inv`. If a nullable state is genuinely required, expose it through `RcuOption` and its `Option`-returning guard API rather than weakening `Rcu`.

## Medium

No findings.

## Low

No findings.

## Evidence check record

- Read all 191 lines of the supplied `diff.patch` and checked the affected definitions in both `before/` and `after/` context.
- Confirmed statically that the only post-change public `new_none` definition in `ostd/src/sync/rcu/mod.rs` is on `Rcu<P>`, while `ostd/src/sync/rcu/non_null/either.rs:565` still calls `RcuOption::new_none()`.
- Traced the null state through `RcuInner::new_none`, `Rcu::read`, and `RcuReadGuard::get`; the latter unconditionally unwraps the optional inner reference.
- Checked the patch for `#[verifier::rlimit(...)]` changes and newly added or materially changed `std`/`core`/`alloc` external specifications; neither workflow trigger is present.
- Per the fast-review constraint, no history inspection, sub-agent pass, Verus run, build, test, or isolated caller experiment was performed. Findings are based on static source evidence only.
