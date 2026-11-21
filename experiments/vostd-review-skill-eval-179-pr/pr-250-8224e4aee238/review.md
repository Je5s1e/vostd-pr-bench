# Review: PR 250 isolated diff snapshot

> Produced from the VOSTD review skill's proof-engineering and API-contract criteria.
> Scope: `pr-250-8224e4aee238/diff.patch` is authoritative (142 lines), with the matching `before/` and `after/` trees used only for context. This was a fast, non-exhaustive static review.

**Bottom line:** The patch does not actually discharge `entails_not_temp_reverse`: it replaces the former `admit()` with an `assume` for a satisfiability condition that is absent from the lemma's contract. The advertised implication is false for an unsatisfiable `spec`, and the lemma is exported in broadcast groups, so this remains a repository-wide trusted inconsistency. This should block merging until the contract or theorem is corrected and the assumption is removed.

## High

### `entails_not_temp_reverse` assumes the missing condition needed to make its public theorem true

- **Guidelines:** `api-preconditions`; `centralize-trusted-boundaries`
- **Location:** `vstd_extra/src/temporal_logic/rules.rs:849`
- **Quoted evidence:**

  ```rust
  pub broadcast proof fn entails_not_temp_reverse<T>(spec: TempPred<T>, p: TempPred<T>)
      requires
          #[trigger] spec.entails(not(p)),
      ensures
          !spec.entails(p),
  {
      assume(exists|ex| spec.satisfied_by(ex));
  ```

  `entails` is universal implication (`defs.rs:147-149`), and `valid` quantifies over every execution (`defs.rs:240-242`). The repository also defines an unsatisfiable predicate as `false_pred()` (`defs.rs:248-250`). Consequently, choosing `spec = false_pred()` makes both `spec.entails(not(p))` and `spec.entails(p)` true for any `p`: their implication antecedent is always false. The stated postcondition `!spec.entails(p)` is therefore false for this legal input. The new `assume` supplies exactly the missing satisfiability premise without exposing it to callers. The lemma is included in both `group_definition_basics` (`rules.rs:882-897`) and public `group_tla_rules` (`rules.rs:3400-3413`), magnifying the trust impact.
- **Problem:** Replacing the prior `admit()` with this `assume` neither verifies the theorem nor preserves a sound caller-visible contract. It silently treats satisfiability as true and lets a broadcast rule establish a false proposition for an unsatisfiable specification.
- **Suggestion:** Add an explicit satisfiability precondition such as `exists|ex| spec.satisfied_by(ex)` and use that premise in the proof, or reformulate the result so it remains valid for inconsistent/unsatisfiable specifications. Remove the `assume`; if callers cannot establish satisfiability, keep this rule out of the broadcast groups rather than hiding the obligation.

## Medium

No findings.

## Low

No findings.

## Evidence check record

- Read all of the authoritative patch and inspected the corresponding before/after context for all four changed hunks.
- Checked the definitions of `TempPred::entails`, `valid`, `not`, and `false_pred`, plus both broadcast-group exports. The concrete `false_pred()` counterexample statically refutes the theorem under its current precondition.
- Searched the snapshot for uses of `entails_not_temp_reverse`, `absorb_or`, and changed assumptions. No separate reuse, rlimit-over-200, or changed `std`/`core`/`alloc` external-spec finding was supported.
- The standalone guideline pages named by the skill were not present in this isolated PR snapshot; the finding is grounded in the skill-defined `api-preconditions` criterion and the bundled proof-engineering trust-boundary criterion.
- **No verification disclosure:** Per the requested fast-review scope, I did not run Verus, compile the repository, inspect Git history, or execute standalone/client experiments. Conclusions are based only on static evidence from `diff.patch` and the supplied before/after trees.
