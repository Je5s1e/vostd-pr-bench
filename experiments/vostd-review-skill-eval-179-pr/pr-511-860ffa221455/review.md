# Review: PR 511 finite-set migration

> Produced from the VOSTD API-contract criteria, using `diff.patch` and the captured before/after trees.
> Scope: `pr-511-860ffa221455/diff.patch` (SHA-256 `6bc362b3fa40b915298bbbf0c6f59491f188b2c40c1029e54f67fe18c64ee7c4`).

**Bottom line:** The mechanical migration is generally consistent with the new finite `Set` API, but one public proof helper loses support for arbitrary predicate-defined domains even though its theorem does not require finiteness. Preserve that general API with `ISet` (or an equivalent predicate-level contract) instead of forcing callers to provide a finite `Set`.

## High

No high-severity findings.

## Medium

### Preserve the predicate-wide contract of `lemma_empty_bad_set_implies_forall`

- **Guideline:** `api-preconditions`
- **Location:** `verified_libs/vstd_extra/src/set_extra.rs:98`
- **Evidence:** Before this patch, the public lemma accepted arbitrary predicates and concluded `forall|x: T| p(x) ==> q(x)` from `Set::new(|x: T| p(x)).filter(|x| !q(x)).is_empty()` (`before/.../set_extra.rs:109-121`). The replacement takes `s: Set<T>` and concludes only `forall|x: T| s.contains(x) ==> q(x)` (`after/.../set_extra.rs:97-109`). Unlike the adjacent `lemma_full_good_set_implies_forall`, the old empty-bad-set lemma had no `finite()` premise and its contradiction proof does not depend on cardinality.
- **Problem:** This is not just a representation update: it removes the useful case where `p` denotes an arbitrary, potentially infinite domain. A natural caller proving `forall x, p(x) ==> q(x)` can no longer instantiate the helper unless the domain can be represented as the new finite `Set<T>`, even though finiteness is unnecessary for the theorem.
- **Suggestion:** Keep this helper predicate-wide by representing the bad set with `ISet` (for example, accept `p` and `q` as before and state emptiness using an `ISet` filter), or state the premise directly as `forall|x| p(x) ==> q(x)`'s equivalent no-counterexample form. The cardinality-based `lemma_full_good_set_implies_forall` may remain on finite `Set`.

## Low

No low-severity findings.

## Evidence check record

- Static review used the complete supplied patch and inspected both captured versions around the changed contracts and representative migration sites.
- The premise above was checked against the old and new signatures and bodies: only the adjacent length-based helper needs finiteness; the reported helper uses no length/cardinality reasoning.
- No changed `#[verifier::rlimit(...)]` annotation was present, so the `rlimit > 200` workflow check did not trigger. No new or materially changed external specification for a `std`, `core`, or `alloc` API was present.
- No Verus run, client experiment, history inspection, CI run, or exhaustive guideline checklist was performed, per the requested fast-review override. The captured directory does not contain the repository's coding-guideline pages, so no maintainability/proof-engineering issue was reported without an available rule text.
