# Review: PR 355 snapshot `2a3429fb0b20`

> Produced from the VOSTD coding-guideline criteria and the skill's API-contract criteria.
> Scope: fast, non-exhaustive static review of the authoritative `diff.patch`; the supplied `before/` and `after/` trees were used only for surrounding context. Changed paths: `ostd/src/sync/mod.rs`, `ostd/src/sync/rwlock.rs`, `vstd_extra/src/resource/ghost_resource/csum.rs`, `vstd_extra/src/resource/ghost_resource/tokens.rs`, and `vstd_extra/src/sum.rs`.

**Bottom line:** This patch is not mergeable as written. It removes the public `RwArc`/`RoArc` API from `ostd::sync`, and the edited `RwLock` module contains three malformed generic parameter lists that prevent the module from parsing. Restore the public module/export and correct the affected negative `Send` implementations before merging the proof-resource refactor.

## High

### The patch removes `RwArc` and `RoArc` from the compiled public API

- **Guideline:** `preserve-exec-code`
- **Location:** `ostd/src/sync/mod.rs:6`, `ostd/src/sync/mod.rs:16`
- **Quoted evidence:** Before the patch, the module contains `mod rwarc;` and publicly re-exports `rwarc::{RoArc, RwArc}`. The after-image changes those exact declarations to `//mod rwarc;` and `//rwarc::{RoArc, RwArc},`. The implementation still exists in `ostd/src/sync/rwarc.rs`, but it is no longer compiled or reachable through `ostd::sync`.
- **Problem:** This is an executable and source-compatibility regression, not a proof-only refactoring. Every downstream import or use of `ostd::sync::{RwArc, RoArc}` loses the types entirely, including all of their runtime behavior.
- **Suggestion:** Keep `mod rwarc;` and the `pub use` entry active. If the rewritten `RwLock` proof representation temporarily prevents `rwarc.rs` from verifying, preserve the executable API behind a narrow, documented verification boundary rather than removing the module from compilation.

### The rewritten `RwLock` module has invalid `impl` syntax

- **Guideline:** `preserve-exec-code`
- **Location:** `ostd/src/sync/rwlock.rs:694`, `ostd/src/sync/rwlock.rs:699`, `ostd/src/sync/rwlock.rs:704`
- **Quoted evidence:** The patch changes all three negative auto-trait implementations to `impl<T /*?Sized*/,, G: SpinGuardian> !Send ...`, with two consecutive commas in the generic parameter list: one each for `RwLockWriteGuard`, `RwLockReadGuard`, and `RwLockUpgradeableGuard`.
- **Problem:** A generic parameter list cannot contain an empty parameter between two commas. These active declarations therefore prevent `rwlock.rs` from parsing, so neither Rust compilation nor Verus verification can reach the new invariant and ghost-resource proofs.
- **Suggestion:** Remove the extra comma in each declaration, yielding `impl<T /*?Sized*/, G: SpinGuardian> !Send ...`, and run the normal formatter/build/verification checks after the correction.

## Medium

No medium-severity findings.

## Low

No low-severity findings.

## Evidence check record

- Read the complete 2,336-line `diff.patch` as the authoritative change set and inspected the corresponding before/after context for all five changed paths. The patch has SHA-256 `8ae1c99bcdfd9c98d0a1102e7fde51ac9e93c788e44687ac4994ee675faf1ce2`.
- Refutation check for the API-removal finding: the after-tree retains `ostd/src/sync/rwarc.rs`, but the only module declaration and public re-export in `ostd/src/sync/mod.rs` are both commented out. Source remaining on disk does not make the types part of the compiled crate.
- Refutation check for the syntax finding: searched every added line in the patch for consecutive commas. The three active negative `Send` implementations are the only matches, and each is present verbatim in the after-image at the reported line.
- Searched the full patch for `admit`, `assume`, `#[verifier::rlimit(...)]`, `external_fn_specification`, and `assume_specification`; none is added or changed. The `rlimit > 200` and upstreamable `std`/`core`/`alloc` external-spec checks are therefore not triggered.
- The new `csum`, token-resource, and `Sum` proof helpers have explicit tracked-resource contracts and introduce no visible assumption or trusted-body marker in the patch. This fast static pass found no additional strong, evidence-backed contract or invariant defect in them.
- **No-verification disclosure:** Per the requested fast-review override, no subagents were used, no Git history was inspected, no exhaustive guideline checklist was performed, and no Rust build, Verus run, test, or isolated caller/spec experiment was executed. The findings are based solely on static evidence in `diff.patch` and the supplied before/after snapshots.
