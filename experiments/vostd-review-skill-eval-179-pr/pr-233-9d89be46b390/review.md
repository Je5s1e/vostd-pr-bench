# Review: PR #233, `8bfa0d130f00..9d89be46b390`

> Produced from the VOSTD coding-guideline criteria requested for this fast review.
> Scope: authoritative `diff.patch`; comparison base `8bfa0d130f004b5dd4b3a0e418b8c6b6b01d74dd`, head `9d89be46b390baf213ffca2b82183f6ef253020c`; before/after snapshots were used only as surrounding context.

**Bottom line:** The change correctly removes a duplicate `injective_on` definition in favor of `vstd::relations::injective_on`, but it does not complete that migration for an existing downstream caller. The unchanged caller obtains `function_properties` items through `vstd_extra::prelude::*` and still names `injective_on` unqualified, so deleting the public definition removes that name from its scope. This is merge-blocking until the caller explicitly imports the vstd predicate (as the recorded direct-child repair does).

## High

### The reused predicate is no longer in scope at an existing caller

- **Guideline:** `reuse-existing-specifications`
- **Location:** `vstd_extra/src/function_properties.rs:7` (deleted definition); downstream manifestation at `lock-protocol-rcu/src/spec/utils.rs:1164`
- **Quoted evidence:** The patch deletes `pub open spec fn injective_on<A, B>(...)`. The unchanged caller imports `use vstd::prelude::*;` and `use vstd_extra::prelude::*;`, then states `injective_on(|trace| Self::get_subtree_traces(trace), Self::valid_trace_set())`. `vstd_extra/src/prelude.rs:11` only has `pub use super::function_properties::*;`; after the deletion, that glob no longer exports `injective_on`. In contrast, the changed module itself can still resolve the predicate because `vstd_extra/src/function_properties.rs:2` has `use vstd::relations::*;`.
- **Problem:** Reusing the canonical vstd predicate is appropriate, but the patch changes the public name-resolution surface without updating this caller. Static import/export inspection therefore shows that the caller loses its unqualified `injective_on` binding.
- **Suggestion:** Add `use vstd::relations::injective_on;` to `lock-protocol-rcu/src/spec/utils.rs` in the same change. The exported direct-child repair `aa2547b7ff107ddfdfb3ac756740473faeb3e093` makes exactly this correction.

## Medium

No findings.

## Low

No findings.

## Evidence check record

- Read the complete authoritative patch (SHA-256 `69af1e1f893e52024d67da978bbb82d217952711a7b8d9b07a16d8fe695e4515`): it contains only the deletion of the public `injective_on` definition.
- Compared the complete before/after `vstd_extra/src/function_properties.rs` snapshots and checked the unchanged `vstd_extra/src/prelude.rs` export plus the unchanged caller imports and use at `lock-protocol-rcu/src/spec/utils.rs:1164`.
- Tried to refute the scope-loss premise: the changed module has its own private `use vstd::relations::*;`, but neither the caller nor `vstd_extra::prelude` publicly re-exports that private import. The recorded direct-child repair independently corroborates the required explicit import.
- No `#[verifier::rlimit(...)]` change is present, and the patch adds or changes no `std`, `core`, or `alloc` external specification.
- Per the requested fast-review override, no history investigation, Verus run, compilation, isolated caller experiment, or exhaustive guideline checklist was performed. The finding is based on static name-resolution evidence and the supplied repair record; CI/verification status was not independently checked.
