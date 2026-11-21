# Review: PR 350 snapshot `5cbda0832ce0` (snapshot `pr-350-5cbda0832ce0`)

> Produced from the VOSTD coding-guideline criteria available to this review.
> Scope: authoritative `diff.patch`, with `before/` and `after/` used only as surrounding context; changed path `ostd/src/sync/rwarc.rs`.

**Bottom line:** This change is not mergeable because it comments out a substantial part of `RwArc`'s executable API merely to leave a simpler fragment under verification. `RwArc::get`, `Clone`, `Drop`, and `get_cloned` disappear from the compiled module, while the newly enabled `ktest` and the public type documentation still rely on that API. Restore the executable behavior and verify it incrementally instead of excluding it with block comments.

## High

### The verification change removes the core `RwArc` API and leaves its enabled test uncompilable

- **Guideline:** `preserve-exec-code`
- **Location:** `ostd/src/sync/rwarc.rs:66`
- **Quoted evidence:** The after-image starts a block comment immediately before `pub fn get` (`/*` at line 66), closes it after `get_cloned` at line 130, and therefore excludes `get`, `impl Clone for RwArc<T>`, `impl Drop for RwArc<T>`, and `get_cloned` from compilation. At the same time, lines 142-159 enable `#[cfg(ktest)]` code that calls `rw1.get()`, `rw1.clone()`, and `drop(rw2)`. The retained public rustdoc at lines 22-25 also says the type exists to provide lockless access and links to the now-absent `RwArc::get` method.
- **Problem:** This is a caller-visible behavioral and source-compatibility regression, not a proof-only refactoring. Under `ktest`, method resolution for `get` and `clone` has no corresponding compiled implementation; outside tests, downstream callers lose those public operations and `num_rw` no longer tracks multiple `RwArc` owners because the only increment/decrement implementations were commented out.
- **Suggestion:** Remove the block comments, retain the original `get`, `Clone`, `Drop`, and `get_cloned` executable code, and model the atomic counter transitions needed to verify those implementations. If some operations cannot yet be proved, keep their executable bodies and use a narrow, explicitly documented temporary verification boundary rather than deleting the API from the compiled program. Keep the test enabled only once it compiles against the restored API.

## Medium

No medium-severity findings.

## Low

No low-severity findings.

## Evidence check record

- Read all 105 lines of `diff.patch`; it changes only `ostd/src/sync/rwarc.rs` and contains no `#[verifier::rlimit(...)]` change or new external specification for a `std`, `core`, or `alloc` API.
- Compared the complete 149-line before-image with the complete 161-line after-image. The removed methods are present as compiled items before the patch and remain only as block-comment text afterward.
- Searched the after-image for `RwArc` consumers. The newly enabled `ktest` at lines 142-159 is a direct in-file caller of the excluded `get` and `Clone` implementations, while the module continues to export `RwArc` and `RoArc` from `ostd/src/sync/mod.rs`.
- Checked the neighboring verified `RwLock` implementation for context: its `read` and `write` methods remain executable, so the concern is specifically the exclusion of `RwArc` behavior, not a requirement to preserve an obsolete dependency.
- No Verus run, Rust build, test execution, history inspection, or isolated client experiment was performed, per the fast-review constraints. The finding is based on static source and conditional-compilation evidence only.

