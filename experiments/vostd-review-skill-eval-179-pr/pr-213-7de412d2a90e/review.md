# Review: `diff.patch` snapshot

> Fast, non-exhaustive VOSTD review based on `diff.patch` and the supplied `before/` and `after/` trees.
> Scope: `diff.patch` SHA-256 `d48ca17ff24ad8803d694d30486f23aece3d2b72db3371fb83aa41b355d32167`; no branch or commit metadata was supplied.

**Bottom line:** The PR should not merge while its advertised starvation-freedom result is obtained through two `admit()` holes, including a wholly admitted top-level theorem. The patch also introduces two independently maintained encodings of the same mutex state machine, creating an immediate model-drift risk. No excessive `rlimit` or new standard-library external specification was found in the patch.

## High

### Starvation freedom is trusted rather than proved

- **Guideline:** `centralize-trusted-boundaries`
- **Location:** `specs/ostd/src/sync/abstract_lock.rs:432`, `specs/ostd/src/sync/abstract_lock.rs:450`
- **Evidence:** `lemma_starvation_free_case1` closes its per-thread liveness assertion with `by { admit(); }`, and `lemma_starvation_free` has the body `{ admit(); }` while ensuring `spec.entails(starvation_free())` (lines 440–450).
- **Problem:** These holes make the central liveness claim available as a proved lemma without deriving it from the stated transition and fairness assumptions. Keeping the admits next to the model also expands the trusted surface outside a deliberate, documented trust-boundary module and can make downstream proofs appear verified when they depend on an unproved theorem.
- **Suggestion:** Complete both proofs before merging. If the theorem is intentionally provisional, do not expose it as a proved lemma: remove or gate it, or move the explicitly reviewed assumption into the repository's centralized external/trust boundary with documentation that identifies the exact unproved fact and its consumers.

## Medium

### The mutex transition system is duplicated in two competing models

- **Guideline:** `reuse-existing-specifications`
- **Location:** `specs/ostd/src/sync/mod.rs:3-4`
- **Evidence:** Both `pub mod mutex;` and `pub mod mutex_verussync;` are compiled. `mutex.rs:37-46` and `mutex_verussync.rs:38-47` declare the same eight state fields; their initializers (`mutex.rs:48-59`, `mutex_verussync.rs:49-59`) agree; and corresponding transitions repeat the same guards and updates—for example `enqueue_waker`/`enqueue_waker_inc_waker` at `mutex.rs:101-137` and `mutex_verussync.rs:84-100`, and `start`/`cs` at `mutex.rs:282-336` and `mutex_verussync.rs:183-210`.
- **Problem:** There is no bridge or stated division of responsibility between the handwritten `Action` model and the `state_machine!` model. Any future semantic correction must be made twice, and proofs can silently target a model that has drifted from the other one.
- **Suggestion:** Select one encoding as the canonical mutex specification and build proofs and adapters on it. If both encodings are required for a migration or comparison, keep one as a generated/derived view or add an explicit refinement/equivalence relation and document which model is authoritative.

## Low

| Finding | Guideline | Detail |
|---|---|---|
| Module-wide lint suppression | `narrow-lint-suppressions` | `specs/ostd/src/sync/mod.rs:1` applies `#![allow(non_camel_case_types)]` to the whole module subtree to accommodate lowercase model labels. Rename the variants, or apply an item-level `#[expect(non_camel_case_types)]` to each deliberately nonconforming enum so future occurrences are not silently hidden. |

## Evidence check record

- Inspected the complete changed-path inventory and all `diff.patch` hunks with targeted static searches, then read the relevant supplied `after/` source around each reported location. The files behind the findings are new, so there is no corresponding `before/` implementation to reconcile.
- Searched the supplied after-tree for `admit`, `assume`, axioms, external bodies/specifications, and verifier rlimits. The only trust holes found were the two reported `admit()` calls. No `#[verifier::rlimit(...)]` was present, so the `> 200` workflow check did not trigger. No new or changed external specification for a `std`, `core`, or `alloc` API was found, so the upstream-reuse workflow check did not trigger.
- Checked the duplicate-model premise against concrete field, initializer, guard, and transition-update definitions in both files; the finding does not rest on filename similarity alone.
- API-contract review was limited to obvious static issues in the changed spec/proof APIs. No separate high- or medium-confidence `api-preconditions` or `api-postconditions` defect was established in this fast pass.
- **No-verification disclosure:** Per the requested fast-review constraints, this review did not run Verus, Z3, builds, tests, isolated caller experiments, git history analysis, child/persona agents, or an exhaustive rule-by-rule audit. Findings are therefore static and evidence-backed, but verification status and proof feasibility were not independently tested.
