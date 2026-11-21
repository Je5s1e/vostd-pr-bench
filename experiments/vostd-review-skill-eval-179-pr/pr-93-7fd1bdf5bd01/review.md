# Review: PR 93 captured patch (`vstd_extra/src/manually_drop.rs`)

> Scope: fast isolated review of the authoritative `diff.patch`, with the captured `before/` and `after/` trees used only for surrounding context. The patch changes the external specification of `core::mem::ManuallyDrop`; no `#[verifier::rlimit(...)]` change is present.

**Bottom line:** The captured after-tree has a hard integration break: the patch deletes `ex_manually_drop_value_axiom`, but an unchanged verified caller still imports it. The constructor specification also loses its `when_used_as_spec` mapping, so callers can no longer naturally use `ManuallyDrop::new(...)` as a specification expression even though the patch continues to provide such mappings for `deref` and `into_inner`. Both issues should be fixed before merge.

## High

### Deleting a live exported proof API leaves an unresolved in-tree use

- **Guideline:** `defer-auxiliary-proof-functions`
- **Location:** `vstd_extra/src/manually_drop.rs:35` (the deletion beginning at old line 35)
- **Quoted evidence:** The patch removes `pub broadcast axiom fn ex_manually_drop_value_axiom<V: Sized>(value: V)`, while the captured after-tree still contains `broadcast use vstd_extra::manually_drop::ex_manually_drop_value_axiom;` at `fvt5-lifecycle-safety/src/page/mod.rs:405`.
- **Problem:** This helper is not unused auxiliary proof code: it is an exported proof API with a live in-tree consumer. Removing the definition without changing that consumer leaves an unresolved path and prevents the captured tree from compiling/verifying.
- **Suggestion:** Update `from_raw` in the same change so it no longer imports the deleted axiom and obtains the needed `ManuallyDrop` fact from the new constructor contract, or retain a compatibility lemma with the old name until all callers have migrated.

## Medium

### `ManuallyDrop::new` loses its specification-expression mapping

- **Guideline:** `api-postconditions`
- **Location:** `vstd_extra/src/manually_drop.rs:15`
- **Quoted evidence:** Before the patch, the constructor external spec has `#[verifier::when_used_as_spec(ex_manually_drop_new_spec)]`; after the patch, line 15 begins directly with `pub assume_specification<T>[ ManuallyDrop::new ]...` and only `returns manually_drop_new_spec(v)`. In the same after-file, `deref` retains `#[verifier::when_used_as_spec(manually_drop_deref_spec)]` at line 22 and `into_inner` retains `#[verifier::when_used_as_spec(manually_drop_unwrap)]` at line 30.
- **Problem:** The `returns` clause describes an executed call's result, but the removed attribute was the mapping that allowed the Rust constructor itself to be used in spec expressions. This regresses the natural proof API and prevents contracts and lemmas from stating compositions such as `ManuallyDrop::into_inner(ManuallyDrop::new(v))` using the actual API names.
- **Suggestion:** Restore `#[verifier::when_used_as_spec(manually_drop_new_spec)]` on the `ManuallyDrop::new` external specification, keeping the new `ensures` relation as well.

## Low

No low-severity findings.

## Evidence check record

- Read all 81 lines of `diff.patch`; it changes only `vstd_extra/src/manually_drop.rs`.
- Compared the complete captured before/after versions of that file. The old exported axiom and the constructor's `when_used_as_spec` attribute are both removed by the patch.
- Searched the complete captured before/after trees for the removed `ex_manually_drop_*` names. The after-tree still has the live import at `fvt5-lifecycle-safety/src/page/mod.rs:405`; no replacement definition exists in the captured after-tree.
- Checked the new three-operation contract locally: `new` returns `manually_drop_new_spec(v)` and relates its dereference to `v`; `deref` and `into_inner` retain explicit spec-call mappings. No independent evidence in the captured tree refutes either finding.
- No `#[verifier::rlimit(...)]` addition or change appears in the patch, so the numeric `rlimit > 200` check is not triggered.
- The changed item is itself a local external specification for a standard-library API. The limited captured tree contains no vendored `vstd`, upstream repository, or other authoritative active specification root from which to establish a duplicate/reuse finding; none is reported.
- **No-verification disclosure:** Per the requested fast-review override, no Verus run, build, caller experiment, history inspection, network lookup, or exhaustive guideline pass was performed. Findings are based solely on the authoritative patch and captured before/after source evidence.
