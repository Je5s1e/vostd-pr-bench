# Review: `diff.patch` (`before` → `after`)

> Produced from the VOSTD maintainability and proof-engineering criteria, with focused API-contract and invariant checks.
> Scope: the complete 198-line `diff.patch` and the corresponding before/after versions of `lock-protocol/src/exec/rw/cursor.rs`. This was a fast, non-exhaustive static review.

**Bottom line:** The patch is not merge-ready because the `GuardInPath::None` rename was applied inconsistently. Six specifications and loop invariants still name the removed variant, so the changed module cannot be parsed/verified as written. No additional high-confidence contract, trust-boundary, specification-reuse, or rlimit issue was found in the scoped change.

## High

### The removed `None` variant remains in cursor invariants

- **Guidelines:** `preserve-exec-code`, `implement-inv-for-models`
- **Location:** `after/lock-protocol/src/exec/rw/cursor.rs:62`
- **Evidence:** `GuardInPath` now declares `Read`, `Write`, `ImplicitWrite`, and `Unlocked` at lines 26–30, but `Cursor::wf` still says `self.path[level - 1] is None` at line 62. The same stale `GuardInPath` variant test remains in `wf_unlock` (line 92), `wf_with_lock_protocol_model` (line 101), both `lock_range` loop contracts (lines 313 and 337), and the `unlock_range` loop invariant (line 579). These are distinct from the valid `Option::None` and `Child::None` uses elsewhere in the file.
- **Problem:** `None` is no longer a variant of `GuardInPath`. Because these expressions test values whose type is `GuardInPath`, the rename leaves the module with invalid specifications instead of a consistently stated cursor invariant; this blocks parsing/verification and prevents establishing the public `lock_range`/`unlock_range` contracts.
- **Suggestion:** Replace those six `GuardInPath`-typed `is None` tests with `is Unlocked`, including the negated test at line 101 (`!(... is Unlocked)`). Keep the `Option::None` and `Child::None` occurrences unchanged, then run the normal module verification gate.

## Medium

No findings.

## Low

No findings.

## Evidence check record

- Read `diff.patch` in full and compared it against both complete 610/612-line before/after files.
- Used type context to separate the six stale `GuardInPath::None` tests from legitimate `Option::None`, `Child::None`, and lock-protocol model states named `WriteLocked`.
- Checked the new `ImplicitWrite` match coverage and the updated `take`/`take_guard` postconditions; no separate evidence-backed defect was established from those changes alone.
- The patch contains no added or changed `#[verifier::rlimit(...)]` and no new or materially changed external specification for a `std`, `core`, or `alloc` API.
- No Verus run, build, history inspection, caller experiment, isolated proof experiment, or exhaustive guideline checklist was performed, as required by this fast-review scope. The blocking finding is based on direct static source evidence and still requires normal CI/module verification after correction.
