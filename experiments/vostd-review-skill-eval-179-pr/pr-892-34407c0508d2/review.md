# Review: PR 892 snapshot 34407c0508d2

> Fast, non-exhaustive review of `diff.patch` with the supplied `before/` and `after/` trees as context. The review covers maintainability, proof/trust engineering, assumptions, API contracts, invariants, `rlimit > 200`, and specification reuse.

**Bottom line:** No strong evidence-backed high-, medium-, or useful low-severity issue was found in the reviewed diff. The central change consistently couples raw-pointer access with `ExposedPointsTo`, whose invariant relates the access permission to the exposed provenance, and the new helper contracts pin reconstructed pointers and borrowed values. This conclusion is limited to static inspection; no Verus or build verification was run.

## High

None.

## Medium

None.

## Low

None.

## Evidence check record

- Read all 1,036 lines of `diff.patch` and inspected relevant before/after context for the changed frame representation, metadata-slot callers, and the new raw-pointer permission module.
- Checked the new invariant and constructor at `verified_libs/vstd_extra/src/raw_ptr.rs:11-53`: `type_inv` ties `PointsTo` provenance to `IsExposed`, and `new` requires that equality while preserving pointer, initialization, and value observations.
- Checked the public helper contracts at `verified_libs/vstd_extra/src/raw_ptr.rs:57-125`: address reconstruction returns the permission's exact pointer; immutable borrowing requires pointer identity and initialization and returns the permission value; mutable borrowing additionally relates the final permission value and pointer to the returned reference.
- Checked representative migration sites at `ostd/src/mm/frame/mod.rs:118-126`, `ostd/src/mm/frame/mod.rs:554-578`, and `ostd/src/mm/frame/meta.rs:318-344`: the runtime pointer representation and tracked permission move together, and address reconstruction is guarded by the permission's recorded address.
- Searched the patch for `assume`, `admit`, new axioms, trusted-boundary attributes, external specifications, and `#[verifier::rlimit(...)]`. The patch adds no assumption/admission, no external specification, and no rlimit change; the only displayed axiom call is pre-existing context in `meta.rs`.
- Searched the after tree for competing `ExposedPointsTo`/exposed-provenance wrappers. No equivalent local abstraction was found; the wrappers intentionally compose vstd's `PointsTo`, `IsExposed`, `with_exposed_provenance`, `ptr_ref`, and `ptr_mut_ref` rather than introducing a second memory model.
- API-contract review found no concrete natural caller excluded by the new preconditions and no changed output left materially unconstrained. The pointer-producing helpers use exact `returns` clauses, and the mutable borrow pins both the returned value and final permission state.
- **No-verification disclosure:** Per the requested fast-review constraints, no Verus invocation, build, test, isolated caller experiment, history analysis, or exhaustive guideline checklist was performed. Results are based only on static diff and before/after source inspection.
