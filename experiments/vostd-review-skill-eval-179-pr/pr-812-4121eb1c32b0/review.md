# Review: PR #812 snapshot (`diff.patch`)

> Produced from the VOSTD coding-guideline criteria and the skill's API-contract criteria.
> Scope: fast, non-exhaustive review of the changes captured in `diff.patch`, using the corresponding `before/` and `after/` trees for context.

**Bottom line:** The new `AtomicCpuId` abstraction cannot be used by verified callers as constructed: `Default` discards the only `PermissionU32`, while every operation requires a reference to that permission. The patch also weakens the observable contract of `set_if_is_none`, removes the `Task` scheduling-info bridge while publishing the module, and changes the executable atomic ordering solely as part of the proof-oriented rewrite. These issues should be addressed before merge.

## High

### The constructor discards the permission required by every operation

- **Guidelines:** `api-preconditions`, `preserve-exec-code`
- **Location:** `ostd/src/task/scheduler/info.rs:175`
- **Evidence:** `Default::default` returns `Self(PAtomicU32::new(Self::NONE).0)`, retaining only tuple field `.0`. However, `set_if_is_none`, `set_anyway`, and `set_to_none` each introduce `Tracked(perm): Tracked<&mut PermissionU32>` (`:59`, `:100`, and `:126`), and `get` requires `Tracked(perm): Tracked<&PermissionU32>` (`:143`). Their preconditions additionally require that permission's `patomic` identity to equal `self.patomic_id()` (`:61`, `:102`, `:128`, and `:145`). Neither `AtomicCpuId` nor `TaskScheduleInfo` stores or returns the permission.
- **Problem:** `PAtomicU32::new` is the point that creates the matching linear permission, but the public construction path erases it. A verified caller receiving an `AtomicCpuId` has no public proof path to manufacture the identity-matched `PermissionU32`, so all four advertised operations have unobtainable protocol preconditions.
- **Suggestion:** Retain the permission in an ownership model that follows the atomic (for example, in the enclosing scheduler state with a controlled invariant/guard), and make construction return or install both the atomic and its permission. If this API is intended to remain internally synchronized and permission-free for callers, preserve the original `AtomicU32` executable representation and specify that API instead of exposing `PAtomicU32`'s permission protocol through these methods.

## Medium

### `set_if_is_none` does not specify that success means the old value was empty

- **Guideline:** `api-postconditions`
- **Location:** `ostd/src/task/scheduler/info.rs:56`
- **Evidence:** The rustdoc says, “If the previous value is empty, it returns `Ok(())`. Otherwise, it returns `Err(previous_value)`.” The contract only states `ret.is_ok() ==> final(perm).view().value == cpu_id.as_usize() as u32` and, for `Err(prev)`, that `prev@` equals the old value and the value is unchanged (`:65-68`). It never relates the `Ok`/`Err` variant to `old(perm).view().value == Self::NONE`.
- **Problem:** The callable contract permits an `Ok` result for a non-empty old cell and an `Err` result for an empty one. Thus callers cannot use the result to establish the documented compare-exchange decision, which is the purpose of this method.
- **Suggestion:** Add the bidirectional outcome fact, such as `ret.is_ok() == (old(perm).view().value == Self::NONE)`, while retaining the existing payload and final-state guarantees (or express equivalent exhaustive `Ok` and `Err` clauses).

### Publishing `scheduler::info` removes the bridge that makes `Task` schedulable

- **Guidelines:** `preserve-exec-code`, `api-postconditions`
- **Location:** `ostd/src/task/scheduler/info.rs:181`
- **Evidence:** The patch changes `scheduler/mod.rs` from `// pub mod info;` to `pub mod info;`, but comments out the existing `impl CommonSchedInfo for Task { fn cpu(&self) -> &AtomicCpuId { &self.schedule_info().cpu } }` and removes `Task` from the import. The resulting public module still declares `CommonSchedInfo` at `info.rs:188-190`, but `Task` no longer implements it.
- **Problem:** The newly exposed scheduling-info API omits the adapter that connects OSTD's `Task` to its CPU field. Generic schedulers constrained by `T: CommonSchedInfo` cannot use `Task`, and no replacement implementation or documented alternative is introduced.
- **Suggestion:** Restore and verify `CommonSchedInfo for Task`, together with the scheduling state needed to implement `cpu()`. If `Task` integration is intentionally deferred, do not publish this partial module/API in this change.

### The proof-oriented atomic replacement changes runtime ordering

- **Guideline:** `preserve-exec-code`
- **Location:** `ostd/src/task/scheduler/info.rs:80`
- **Evidence:** Before the patch, `compare_exchange`, `store`, and `load` explicitly use `Ordering::Relaxed`. The new calls omit ordering arguments, and the added comment states that `PAtomicU32::compare_exchange` “hardcodes `SeqCst`” (`:80-83`); the stores and load are likewise routed through the replacement `PAtomicU32` API (`:119`, `:136`, `:153`).
- **Problem:** Replacing the runtime atomic solely to obtain a verification permission changes the executable memory-ordering behavior from `Relaxed` to `SeqCst`. The origin comments make the rewrite visible, but do not preserve executable behavior; this can impose unnecessary global ordering and performance costs in scheduler hot paths.
- **Suggestion:** Specify or wrap the original `AtomicU32` operations with their ordering parameters intact. If a permissioned atomic is required, provide operations whose executable lowering preserves the original `Relaxed` ordering and justify that model at the trusted boundary.

## Low

No low-severity findings in this fast pass.

## Evidence check record

- Read `diff.patch` in full and compared the affected files against both `before/` and `after/` context.
- Traced all in-snapshot uses of `AtomicCpuId`, `CommonSchedInfo`, `set_if_is_none`, `set_anyway`, `set_to_none`, and `get`; the permission created by `PAtomicU32::new` is not retained by any changed enclosing type or exposed constructor.
- Checked the newly added `CpuId` conversion/model helpers and found no strong additional issue for this fast report.
- No `#[verifier::rlimit(...)]` change appears in the patch, so the `rlimit > 200` check was not triggered. No new project-local external specification for a `std`, `core`, or `alloc` API appears in scope, so the upstream-spec check was not triggered.
- **Verification disclosure:** Per the requested fast-review constraints, no Verus run, build, tests, history analysis, isolated caller experiment, delegated persona pass, or exhaustive guideline checklist was performed. Findings are based on static source and before/after evidence only.
