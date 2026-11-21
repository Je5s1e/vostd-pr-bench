# Review: PR 860 snapshot (`diff.patch`, before → after)

> Produced from the VOSTD coding-guideline review criteria and the skill's API-contract criteria.
> Scope: fast, non-exhaustive static review of the changes recorded in `diff.patch`, with `before/` and `after/` used only for surrounding context. No history inspection, sub-reviewers, Verus runs, exhaustive checklist, or caller experiments were performed.

**Bottom line:** The new RCU path is generally careful about preserving linear resources and mutable-context state, but the public conditional-update contract drops the one fact a caller needs on the failure path: the returned smart pointer still satisfies the root's publication predicate. The implementation and lower-level contract already retain enough evidence to expose this fact, so the public contract should be strengthened before merge.

## High

No high-severity findings.

## Medium

### Preserve the publication predicate on failed compare-exchange

- **Guideline:** `api-postconditions`
- **Location:** `ostd/src/sync/rcu/irc11.rs:873`
- **Evidence:** The method accepts a replacement only under
  ```rust
  forall|owned: P::Permission| #[trigger]
      value.rel_perm(owned) ==> (self.condition())(owned),
  ```
  but its postcondition constrains only `Ok(Some(pending))`:
  ```rust
  res matches Ok(Some(pending)) ==> pending.inv() && pending.key() == self.root_key()
      && pending.record().removal.observed_by(final(context)@),
  ```
  The failure branch reconstructs and returns the unpublished value (`Err(value)` at lines 916–921). The lower-level CAS explicitly guarantees `res.2@ == ownership` on failure (`ostd/src/sync/rcu/weak_root.rs:560-564`), and `NonNullPtr::from_raw` guarantees `ret.rel_perm(perm@)` (`ostd/src/sync/rcu/non_null/mod.rs:88-94`), but the wrapper does not carry their consequence into its public contract.
- **Problem:** After matching `Err(returned)`, a verified caller cannot prove that `returned` still satisfies `self.condition()`, even though the documentation says the unpublished smart pointer is returned and the implementation preserves its exact permission. In particular, the caller has lost the precondition needed to retry this API with the returned value when the root uses a nontrivial client predicate.
- **Suggestion:** Add an `Err`-arm postcondition preserving the accepted-value relation, for example:
  ```rust
  res matches Err(returned) ==> forall|owned: P::Permission| #[trigger]
      returned.rel_perm(owned) ==> (self.condition())(owned),
  ```
  Keep the existing context and success-ticket guarantees unchanged.

## Low

No low-severity findings.

## Evidence check record

- Read the complete patch and used the `after/` sources for line-numbered surrounding context around the surviving finding.
- Refutation check: followed the failure branch through `RcuWeakRoot::compare_exchange`; its `res.2@ == ownership` guarantee confirms the physical permission is returned, while `NonNullPtr::from_raw` relates the reconstructed value to that permission. These facts support the suggested postcondition but are not exported by `Irc11RcuReadGuard::compare_exchange` itself.
- Trust-boundary scan: the patch adds three `#[verifier::external_body]` sites in `verified_libs/vstd_extra/src/raw_callback.rs`; this fast static pass found no concrete contradiction between their stated private paired-construction boundary and their callers.
- Workflow trigger scan: no added or changed `#[verifier::rlimit(...)]` appears in `diff.patch`, and no project-local external specification for a `std`, `core`, or `alloc` API was added or materially changed. Therefore neither narrow workflow check was triggered.
- **No-verification disclosure:** Verus, Z3, CI, compilation, isolated clients, and controlled variants were not run. This is a fast, non-exhaustive static review, not a verification result or an exhaustive guideline audit.
