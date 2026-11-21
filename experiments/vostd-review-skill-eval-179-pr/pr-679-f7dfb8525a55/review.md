# Review: PR 679 snapshot `f7dfb8525a55`

> Produced from the VOSTD review skill's maintainability, proof-engineering, workflow, and API-contract criteria.
> Scope: `diff.patch` is authoritative, with `before/` and `after/` used only for surrounding context. The patch changes `ostd/specs/mm/embedding/mod.rs` and `ostd/src/mm/frame/linked_list.rs`.

**Bottom line:** The proof decomposition appears to preserve the existing executable API and removes both `rlimit(200)` annotations. I found no high- or medium-severity issue. One small contract-cleanliness issue remains in the new linked-list proof helper: it accepts an unrelated parameter and requires a bound that neither its result nor its proof uses.

## High

None.

## Medium

None.

## Low

| Finding | Guideline | Detail |
|---|---|---|
| Remove the unrelated `nn` obligation from the helper contract | `api-preconditions` | At `ostd/src/mm/frame/linked_list.rs:159-176`, `insert_before_slot_distinct` takes `nn: int` and requires `0 <= nn <= owner0.list.len() as int`, but its `ensures` clause is solely about `owner0`, `regions0`, and `frame_idx`; the proof body at lines 178-189 likewise never references `nn`. This couples a general distinctness lemma to the cursor position for no demonstrated semantic or proof need. Remove the `nn` parameter and its bound, and call the helper with only `owner0.list_own`, `regions0`, and `frame_own.slot_index`. |

## Evidence check record

- Read the complete authoritative 508-line `diff.patch` and inspected the corresponding before/after context for both changed files.
- Confirmed statically that the two changed `#[verifier::rlimit(200)]` annotations are removed; the patch adds no rlimit above 200.
- Confirmed that no executable function body or public executable contract is introduced or materially changed; the patch isolates proof obligations into `#[verifier::spinoff_prover]` helpers.
- Checked the new accounting helper's stated postcondition against the three clauses of `VmStore::accounting_inv` and its call from `step_segment_from_unused`; no evidence-backed contract or invariant regression was identified from the snapshot.
- Checked the new linked-list helper and its sole call. The quoted `nn` parameter/precondition is absent from both the helper's postcondition and proof body, establishing the low-severity finding above by static inspection.
- No new or materially changed external specification for a `std`, `core`, or `alloc` API appears in the patch, so the upstream-spec workflow check was not triggered.
- Per the fast-review constraint, I did not inspect Git history, run Verus, execute caller experiments, or perform exhaustive guideline enumeration. Conclusions are therefore static-review conclusions only; verification status was not independently confirmed.
