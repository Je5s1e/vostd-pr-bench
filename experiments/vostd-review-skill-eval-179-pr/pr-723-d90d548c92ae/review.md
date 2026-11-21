# Review: PR 723 snapshot `d90d548c92ae`

> Produced from the supplied `diff.patch`, with the corresponding `before/` and `after/` trees used only for context. This was a fast, non-exhaustive review limited to maintainability, proof/trust assumptions, API contracts, invariants, rlimit values above 200, and specification reuse.
>
> Scope: `pr-723-d90d548c92ae/diff.patch`; additions to `verified_libs/vstd_extra/src/lib.rs` and `verified_libs/vstd_extra/src/rcu_read_lease.rs`.

**Bottom line:** The accounting design is explicit and no high-severity trust or contract defect is evident from static inspection. Before merge, the registry's intrinsic validity condition should use the standard `Inv` abstraction rather than introducing a parallel public `wf` vocabulary. One smaller layout issue makes the new public API harder to review.

## High

No findings.

## Medium

### Use `Inv` for the registry's intrinsic accounting invariant

- **Guideline:** `implement-inv-for-models`
- **Location:** `verified_libs/vstd_extra/src/rcu_read_lease.rs:509`
- **Evidence:** The registry defines `pub open spec fn wf(self) -> bool` whose clauses refer only to the registry's own fields and derived accessors: active IDs must be below `next_lease`, records must point to contained accumulators with matching identities and positive fractions, and each accumulator plus its active fractions must total one (lines 509–524). Every mutating registry operation then repeats `old(self).wf()` / `final(self).wf()` (for example, `insert` at lines 528–534 and `split_lease` at lines 607–613).
- **Problem:** This is intrinsic validity of a single model, exactly the role standardized by `Inv::inv()`. Keeping it as a bespoke `wf` predicate prevents generic invariant-oriented code from using the registry and establishes a second vocabulary that every caller must learn and propagate.
- **Suggestion:** Implement `Inv for RcuReadLeaseRegistry<K, T, W>` with the current predicate body as `inv()`, and change operation contracts to require `old(self).inv()` and ensure `final(self).inv()`. Retain a separate predicate only if it expresses a relationship to another value; none is present here.

## Low

| Finding | Guideline | Detail |
|---|---|---|
| Defer private recursive bookkeeping lemmas | `defer-auxiliary-proof-functions` | `verified_libs/vstd_extra/src/rcu_read_lease.rs:131` places four private recursive lemmas (`lemma_active_fraction_insert_above`, `lemma_active_fraction_insert_next`, `lemma_active_fraction_remove`, and `lemma_active_fraction_zero`, through line 282) before the public accumulator and registry APIs beginning at line 284. Move these side-obligation helpers after the public API and lifecycle proof so readers encounter the abstraction and contracts before roughly 150 lines of implementation scaffolding. |

## Evidence check record

- Read the complete supplied 932-line patch and inspected the corresponding new file in `after/` with line-numbered context.
- Checked the change for `assume`, `admit`, `external_body`, axioms, unsafe/trusted boundaries, `#[verifier::rlimit(...)]`, and external specifications of `std`, `core`, or `alloc`; none occur in the patch. The rlimit-above-200 and upstream-spec checks therefore produced no finding.
- Traced the conservation invariant through `empty`, `insert`, `split_lease`, `return_lease`, and `reclaim`. Private fields prevent callers from directly fabricating registered leases or active records, and the return contract ties the lease ID, key, accumulator identity, and fraction to its matching record.
- Reviewed public proof API input/output coverage statically. Constructors and transitions expose the key resource identity, fraction, active-ID, frame, and returned-witness facts needed by the next lifecycle operation; no strong evidence-backed precondition or postcondition defect was identified.
- Searched the supplied `after/` verified roots for the introduced type and model names. No competing `RcuLeaseAccumulator`, `RcuReadLeaseRegistry`, or equivalent active-fraction registry was found outside the new module; no specification-reuse finding is supported by this snapshot.
- Attempted to refute the medium finding by checking whether `wf` relates the registry to an external model value. Its body depends only on `self`, so the intrinsic-invariant premise stands.
- **No-verification disclosure:** Per the fast-review instruction, no Verus build, proof experiment, isolated caller experiment, CI run, or history review was performed. Findings are based on static patch and before/after context only; absence of a reported issue is not a verification result.
