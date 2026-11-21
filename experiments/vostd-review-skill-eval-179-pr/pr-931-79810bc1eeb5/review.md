# Review: PR 931 snapshot `79810bc1eeb5` (fast static review)

## Scope

Fast, non-exhaustive review of `diff.patch`, using the supplied `before/` and `after/` trees for context. The review focused on maintainability, proof/trust boundaries, assumptions, API contracts, invariants, `rlimit` values above 200, and specification reuse. Per the requested override, it did not inspect history, delegate persona passes, run Verus, execute isolated caller experiments, or perform the skill's exhaustive checklist.

**Bottom line:** No high- or medium-severity issue was supported by the inspected evidence. One low-severity workflow issue remains: two generally reusable standard-library specifications are being introduced only in VOSTD without an upstream plan.

## High

None.

## Medium

None.

## Low

### Propose the new slice and `Vec` specifications upstream

**Rule:** `upstream-reusable-specs`

**Location:** `verified_libs/vstd_extra/src/external/slice.rs:6-16`; `verified_libs/vstd_extra/src/external/vec.rs:12-25`

The patch adds project-local external specifications for the standard-library implementations `<[T] as AsMut<[T]>>::as_mut` and `<Vec<T, A> as IndexMut<I>>::index_mut`. Both contracts describe generic `core`/`alloc` behavior, contain no VOSTD-specific model, and are reusable by any Verus client that mutably reborrows a slice or indexes a `Vec`. The patch contains no recorded plan to propose them to upstream Verus. Keeping these generic models only in `vstd_extra` creates another trusted contract source that can drift from upstream library models.

Propose both specifications upstream (or reference an existing upstream issue/PR in the change). Keep a temporary local copy only while that work is pending, with the upstream tracking reference recorded beside it.

## Evidence check record

- Read all 442 lines of `diff.patch` and inspected the corresponding before/after source around every changed hunk.
- Compared the new `xmas_elf` type decoding, `get_type`, `get_data`, raw-data slicing, and field getter models with `xmas-elf 0.10.0`'s installed `src/program.rs`. The inspected directions, constants, load-segment result shape, zero-length special case, and overflow/readability guards agree with that implementation; no contradiction strong enough to report was found.
- Compared the new slice `AsMut` and `Vec` `IndexMut` assumptions with the installed Rust standard-library sources. Both executable implementations delegate exactly as the comments state. Their project-local placement, rather than their stated behavior, is the reported issue.
- Checked the `to_flat_binary` precondition, loop invariant, prefix model, overlap behavior, mapping arithmetic, and the only caller. The model matches the unchanged executable order (extend with zeroes, then overwrite file bytes), including preservation of an overlapping segment's existing memory-only tail.
- Searched the supplied after tree for equivalent VOSTD specifications of the two standard APIs and found no duplicate there.
- The patch adds `#[verifier::spinoff_prover]` but no `#[verifier::rlimit(...)]`; therefore there is no changed `rlimit` above 200 to report.
- Candidate concerns about the opaque `Type_` model and conditional `get_data` guarantee were checked against the dependency implementation and refuted by the cited source behavior.

## Verification disclosure

No Verus verification, compilation, tests, isolated caller experiments, network lookups, or repository-history checks were run. Conclusions are from static inspection of the supplied patch, before/after trees, installed `xmas-elf 0.10.0` source, and installed Rust standard-library source. This was intentionally a fast, non-exhaustive review and is not a full skill-compliant verification audit.
