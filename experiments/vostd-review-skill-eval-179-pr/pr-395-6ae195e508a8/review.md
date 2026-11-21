# Review: PR #395 (`6ae195e508a8` snapshot)

> Fast, non-exhaustive review of the supplied `diff.patch`, using the captured before/after trees for context.
> Scope: `pr-395-6ae195e508a8/diff.patch`; changed files are `ostd/src/sync/mod.rs` and `ostd/src/sync/rwmutex.rs`.

**Bottom line:** The patch removes the `Drop` implementations from all three lock guards, so ordinary scope exit and `core::mem::drop` no longer release the lock even though the API remains documented as RAII. It also removes `DerefMut` from the write guard, eliminating the advertised ability to modify protected data. Separately, the proof of reader-count preservation relies on two unchecked overflow assumptions that are not implied by the new atomic invariant.

## High

### Lock guards no longer release the lock on ordinary drop

- **Guideline:** `api-postconditions`
- **Location:** `ostd/src/sync/rwmutex.rs:610`, `:752`, and `:935`
- **Evidence:** The patch removes `impl Drop` for `RwMutexReadGuard_`, `RwMutexWriteGuard_`, and `RwMutexUpgradeableGuard_`, replacing them with inherent methods named `drop(self)`. The resulting file contains no `impl Drop` for any `RwMutex*Guard`. The public documentation still calls these “RAII guards” (`rwmutex.rs:84-87`), says guards are dropped at scope boundaries (`:128`, `:135`), and uses `drop(r1)` / `drop(r2)` (`:119-120`), which invokes `core::mem::drop` rather than an inherent method. The read guard's new inherent `drop` is private as well (`:610`).
- **Problem:** Rust does not call an inherent `drop(self)` method when a value leaves scope. Consequently a normally dropped read, write, or upgradeable guard leaves its lock bit/count held; later acquisitions can block or spin forever, contradicting the central guard API behavior and the examples.
- **Suggestion:** Preserve real `Drop` behavior for executable builds. If current Verus limitations require a manually verified release routine, keep it as a helper and have an actual `Drop::drop` implementation invoke the equivalent release path (using the project's accepted trusted/verified boundary), then add a regression test that reacquires each lock mode after scope exit and after `core::mem::drop`.

### The write guard no longer provides mutable access

- **Guideline:** `api-postconditions`
- **Location:** `ostd/src/sync/rwmutex.rs:643`
- **Evidence:** The diff deletes the complete `DerefMut for RwMutexWriteGuard_` implementation and adds no replacement; the resulting file has only `Deref for RwMutexWriteGuard` at lines 665-676. Yet the type-level documentation promises “`DerefMut` for the writer” (`:84-86`) and both examples mutate through a write guard with `*w1 += 1` and `*w2 += 1` (`:126`, `:133`).
- **Problem:** `RwMutexWriteGuard` can no longer be used to modify `T`; the documented examples and existing callers that assign through the guard will fail to compile. This removes the defining capability of a write lock while continuing to expose `write`, `upgrade`, and `downgrade` as write-guard APIs.
- **Suggestion:** Restore `DerefMut` with a permission-backed mutable borrow and an accurate Verus contract. If mutable borrowing cannot yet be verified, do not enable/export `RwMutex` as a compatible public replacement until the executable API is preserved, and explicitly isolate any temporary trusted boundary.

### Reader-count safety is assumed at the atomic invariant boundary

- **Guideline:** `centralize-trusted-boundaries`
- **Location:** `ostd/src/sync/rwmutex.rs:394` and `:624`
- **Evidence:** Both the `try_read` increment and read-guard release contain `assume(no_max_reader_overflow(prev_usize));`, where `no_max_reader_overflow(v)` is `v & MAX_READER_MASK < MAX_READER_MASK` (`:243-245`). The new lock invariant equates `total_reader_bits` with active plus failed reader attempts (`:181`) but does not require this strict upper bound; its retract-token capacity is `MAX_READER_MASK + 1` (`:26`, `:45`), so saturation is not excluded by the stated invariant. The assumption is then used by `lemma_consts_properties_value` / `lemma_consts_properties_prev_next` to justify arithmetic and the ghost-state transition.
- **Problem:** The proof accepts the key no-wrap premise instead of deriving it from the lock protocol. This leaves the atomic reader-count transition—and therefore the correspondence between lock bits and permissions—outside the established proof, while presenting the implementation as verified.
- **Suggestion:** Strengthen the invariant/protocol so it proves `v & MAX_READER_MASK < MAX_READER_MASK` whenever `fetch_add(READER)` is permitted, or change the executable transition to reject saturation before incrementing and model that branch. Remove both assumptions and prove the increment/decrement obligations from the invariant and token accounting.

## Medium

No medium-severity findings.

## Low

No strong low-severity findings.

## Evidence check record

- Read the complete 1,534-line supplied patch and the full changed `rwmutex.rs` before/after context; checked the public guard definitions, acquisition/release paths, atomic invariant, reader-count lemmas, and module exports.
- Challenged the drop premise against the resulting tree: it contains inherent `drop(self)` methods but no `Drop` implementation for any `RwMutex` guard. Nearby `RwLock` code explicitly labels the same pattern as requiring manual calls, while this API's documentation continues to promise RAII and scope-based release.
- Challenged the write-access premise against the resulting tree: `DerefMut` is imported but no `DerefMut for RwMutexWriteGuard` implementation remains.
- Checked for changed `#[verifier::rlimit(...)]` values and newly added `std`/`core`/`alloc` external specifications; none were found, so the narrow workflow checks do not trigger. No evidence-backed reusable-specification issue was identified.
- The supplied snapshot does not include its own coding-guideline tree. Rule grounding therefore uses the bundled VOSTD review skill's API criteria and trust-boundary rule together with the captured source evidence.
- **No verification disclosure:** Per the fast-review scope, no Verus run, compiler/CI run, proof or caller experiment, repository-history analysis, or exhaustive guideline pass was performed. Findings are static conclusions from the supplied patch and before/after files.
