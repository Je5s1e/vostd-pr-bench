# Review: PR 718 patch `80dcb9bc16eb`

> Scope: the supplied `diff.patch` (SHA-256 `5a7e74d93190b8dc48868f20ce11da90a3dc6c189b76a94ff7476b3d0035e215`) is authoritative, with the supplied `before/` and `after/` trees used only for context.
>
> Review criteria: VOSTD maintainability, proof engineering, API contracts, invariants, `rlimit > 200`, reusable standard-library specifications, and existing-spec reuse, under the requested fast-review limits.

**Bottom line:** The patch gives `range_difference` a meaningful functional model, but its public contract is not yet a faithful, usable abstraction of the generic executable API. In particular, verification adds an execution-level `FiniteRange` restriction, the main result is hidden behind an antecedent the contract does not establish, and the model silently treats cloning as identity. The two new generally reusable `core` specifications should also be proposed upstream.

## High

No high-severity findings.

## Medium

### 1. Verification narrows the executable API to `FiniteRange`

- **Guidelines:** `preserve-exec-code`, `api-preconditions`
- **Location:** `ostd/src/util/ops.rs:70`
- **Evidence:** The original signature was `pub fn range_difference<T: Ord + Copy>` (`before/ostd/src/util/ops.rs:11`), while the patch changes it to `pub fn range_difference<T: Ord + Copy + FiniteRange>`. The executable algorithm only compares, copies/clones, and filters range endpoints; the new `FiniteRange` bound is needed by the set model (`range_as_set<T: FiniteRange>` at `verified_libs/vstd_extra/src/range.rs:42`), not by execution.
- **Problem:** A previously valid `Ord + Copy` endpoint type can no longer call this function unless it also supplies a Verus finite-range model. That is a caller-facing restriction introduced solely to state/prove the set-level postcondition.
- **Suggestion:** Keep the executable function at `T: Ord + Copy` and give it the operational sequence contract, which `range_difference_seq` already states using only `T: Ord`. Put the finite-set correspondence in a separate proof lemma (or another proof-only layer) requiring `T: FiniteRange` and `finite_range_matches_ord::<T>()`.

### 2. The contract does not expose the iterator facts needed to use its result guarantee

- **Guideline:** `api-postconditions`
- **Location:** `ostd/src/util/ops.rs:57`
- **Evidence:** The only `ensures` clause is `ret.obeys_prophetic_iter_laws() && ret.will_return_none() ==> { ... }` (`ostd/src/util/ops.rs:58-68`). Neither `ret.obeys_prophetic_iter_laws()` nor `ret.will_return_none()` is ensured unconditionally. The newly trusted array iterator establishes those facts for `iter` (`verified_libs/vstd_extra/src/external/iter.rs:26-30`), but the returned value is the distinct filtered iterator created at `ostd/src/util/ops.rs:96`.
- **Problem:** A natural verified caller receives no unconditional fact about `ret` and therefore cannot obtain `remaining() == range_difference_seq(*a, *b)`, the length bound, ordering, or set difference without separately proving the contract's own antecedent. The implementation invokes `filter_postcondition`, so at least the filtered iterator laws should be surfaced; completion/value coverage should be expressed using the exact condition provided by the active filter model rather than an unsupported all-or-nothing antecedent.
- **Suggestion:** Ensure `ret.obeys_prophetic_iter_laws()` directly, then guard the exact remaining-sequence properties only by the filter model's actual production/completion predicate (including the predicate closure's return facts). This lets callers use every unconditional property the implementation proves without strengthening termination or panic claims.

### 3. The generic postcondition assumes cloning preserves endpoint values

- **Guidelines:** `complete-external-contracts`, `api-postconditions`
- **Location:** `ostd/src/util/ops.rs:78`
- **Evidence:** For an empty `b`, execution constructs `[a.clone(), b.clone()]` (`ostd/src/util/ops.rs:78-79`), while the claimed result is defined directly from the original values `*a` and `*b` (`ostd/src/util/ops.rs:59`; `verified_libs/vstd_extra/src/range.rs:58-68`). The bounds state only `T: Ord + Copy + FiniteRange` (`ostd/src/util/ops.rs:70`); they contain no logical condition relating a generic `T::clone()` result to its source.
- **Problem:** Rust permits a manual `Clone` implementation even for a `Copy` type, and the type bounds alone do not state the equality that the proof/model needs. Thus the contract models the cloned endpoints as the originals without making that assumption explicit or avoiding it in the executable path.
- **Suggestion:** Prefer a proof/model that follows the actual generic clone relation. If the API intentionally supports only value-preserving clones, add the corresponding explicit clone-law precondition and document the restriction. If preserving the original execution is not required, copying the `Range<T>` values would avoid depending on an unconstrained `Clone`, but that execution change should be evaluated separately because it changes behavior for nonstandard `Clone` implementations.

## Low

| Finding | Guideline | Detail |
|---|---|---|
| The two new project-local `core` contracts are broadly reusable | `upstream-reusable-specs` | `verified_libs/vstd_extra/src/external/iter.rs:23-32` specifies `<[T; N] as IntoIterator>::into_iter`, and `verified_libs/vstd_extra/src/external/range.rs:57-60` specifies generic `Range::<Idx>::is_empty`. Both describe standard-library behavior independently of VOSTD, but the patch records no plan to propose them to Verus upstream. Open or reference upstream proposals and track the local copies until an upstream model can replace them. |

## Evidence check record

- Read the authoritative 455-line patch in full and compared every changed hunk with the supplied before/after files.
- Checked the complete changed implementations and contracts for `range_difference`, the owned-array iterator trust specification, `Range::is_empty`, and the new range models and lemmas.
- Searched the supplied before/after trees for equivalent array-iterator, `Range::is_empty`, and range-difference specifications. No pre-existing equivalent was found in the supplied snapshot; the older `range_usize_is_empty` helper is narrower and does not subsume the new generic standard-library contract.
- The added `#[verus_verify(spinoff_prover, rlimit(50))]` is below the workflow threshold of 200.
- No changed intrinsic model struct or mutable resource invariant was introduced, so no invariant finding is supported by this patch.
- **Verification disclosure:** Per the fast-review instruction, no Verus run, build, test, history inspection, exhaustive rule pass, or isolated caller experiment was performed. Findings are based on static evidence from `diff.patch` and the supplied context trees; verification status and solver behavior remain unconfirmed.
