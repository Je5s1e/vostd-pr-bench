# Review: PR 474 snapshot `a6fdca3a754f`

> Produced from the supplied `diff.patch`, with `before/` and `after/` used only for surrounding context.  
> Scope: fast, non-exhaustive review of `pr-474-a6fdca3a754f/diff.patch`; no repository history, Verus run, isolated caller experiment, or exhaustive guideline enumeration was performed.

**Bottom line:** The patch makes a blocking proof-driven rewrite of the atomic-mode and page-table cursor APIs instead of preserving the executable Rust interface. In particular, it removes live parts of the upstream atomic-mode API, changes the unsafe marker trait's public bound while retaining contradictory rustdoc, and replaces generic guard-bearing cursor APIs with `dyn InAtomicMode` throughout. Restore the executable/API shapes and adapt verification around them before merging.

## High

### Preserve the atomic-mode and cursor API shapes

- **Guideline:** `preserve-exec-code`
- **Location:** `ostd/src/task/atomic_mode.rs:31` (with related API rewrites at `ostd/src/mm/page_table/mod.rs:1645` and `ostd/src/mm/page_table/cursor/mod.rs:86`)
- **Quoted evidence:**

  ```rust
  /* 
  /// Marks a function as one that might sleep.
  ...
  pub fn might_sleep() {
      ...
  }
  */
  ...
  /// It requires [`core::fmt::Debug`] by default ...
  #[verus_verify]
  pub unsafe trait InAtomicMode/* : core::fmt::Debug*/ {}
  /* 
  pub trait AsAtomicModeGuard {
      ...
  }
  ...
  */
  ```

  The same patch changes the cursor representation and public constructor surface:

  ```rust
  -pub struct Cursor<'rcu, C: PageTableConfig, A: InAtomicMode> {
  +pub struct Cursor<'rcu, C: PageTableConfig> {
  ...
  -    pub rcu_guard: &'rcu A,
  +    pub rcu_guard: &'rcu dyn InAtomicMode,
  ...
  -    pub fn cursor_mut<'rcu, G: InAtomicMode>(
  +    pub fn cursor_mut<'rcu>(
           &'rcu self,
  -        guard: &'rcu G,
  +        guard: &'rcu dyn InAtomicMode,
  ```

- **Problem:** The guideline requires proof work to preserve executable Rust and upstream API shapes unless a minimal runtime change is necessary and equivalence is demonstrated. Here, enabling `task::atomic_mode` simultaneously suppresses `might_sleep` and `AsAtomicModeGuard`, removes the documented `Debug` supertrait, and changes the guard/cursor type signatures across the page-table API; the patch provides neither a concrete Verus necessity nor evidence that downstream behavior and source compatibility are unchanged. The retained rustdoc explicitly says that `InAtomicMode` requires `Debug`, contradicting the new declaration.
- **Suggestion:** Restore `might_sleep`, `AsAtomicModeGuard`, the `Debug` supertrait, and the original generic cursor/page-table signatures. Put any Verus-only abstraction in specifications or local proof adapters while retaining the original executable definitions. If a particular executable rewrite is genuinely unavoidable, keep it minimal, include the adjacent original form and concrete limitation required by `preserve-exec-code`, and demonstrate that runtime behavior and caller-facing compatibility are preserved.

## Medium

No evidence-backed findings.

## Low

No evidence-backed findings.

## Evidence check record

- Read the full authoritative 1,023-line `diff.patch` and checked the cited areas against both `before/` and `after/` snapshots.
- Confirmed that the pre-change `InAtomicMode` declaration is `pub unsafe trait InAtomicMode: core::fmt::Debug {}` and that `might_sleep` plus `AsAtomicModeGuard` are executable declarations in the source being modified.
- Confirmed that the patch removes the generic guard parameter from `Cursor`, `CursorMut`, and their page-table/vm-space entry points, replacing it with `&dyn InAtomicMode` rather than limiting the change to ghost/specification code.
- Searched the patch for newly added `assume`, `admit`, `external_body`, and `rlimit` annotations. No changed `#[verifier::rlimit(...)]` was found, and no `rlimit` above 200 was introduced. The added `#[verifier::external]` on the unsafe marker implementation was inspected but not reported separately because the fast static pass did not establish a distinct logical inconsistency beyond the consolidated API-preservation problem.
- No new or materially changed external specification for a `std`, `core`, or `alloc` API was found, so no upstream-spec-reuse finding is reported.
- No separate API-precondition or API-postcondition defect was established: the cursor success/failure and owner-state clauses are largely carried forward while their guard type is rewritten. The interface rewrite is covered by the finding above.
- **No-verification disclosure:** Per scope, this review did not run Verus, Rust compilation, CI, history analysis, or caller experiments. The finding rests on direct before/diff/after source evidence and the `preserve-exec-code` rule; verification status is unknown.
