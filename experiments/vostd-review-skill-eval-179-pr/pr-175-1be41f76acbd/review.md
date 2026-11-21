# Review: PR #175 artifact `1be41f76acbd`

> Produced from the VOSTD coding-guideline criteria in fast, non-exhaustive mode.
> Scope: `pr-175-1be41f76acbd/diff.patch`, with the captured `before/` and `after/` files used for context.

**Bottom line:** The patch moves two generic map facts into public proof helpers but proves both with `admit()`. Because downstream proofs may use their postconditions for arbitrary key and value types, this expands the trusted surface and should block merging until the facts are proved or placed in an explicit, narrowly documented trust boundary. No other strong, evidence-backed issue was found in the requested fast review.

## High

### Public generic map lemmas silently extend the trusted surface

- **Guideline:** `centralize-trusted-boundaries`
- **Location:** `vstd_extra/src/map_extra.rs:441` and `vstd_extra/src/map_extra.rs:456`
- **Quoted evidence:**

  ```rust
  pub proof fn lemma_project_first_key_value_filter_empty<K1, K2, V>(...)
      ...
  {
      admit();
  }

  pub proof fn lemma_project_first_key_finite<K1, K2, V>(...)
      ...
  {
      admit();
  }
  ```

  The first function exports a universally quantified absence result, and the second exports finiteness of the projected domain. Both are generic and public.
- **Problem:** `admit()` causes Verus to trust each `ensures` clause without a proof. Keeping these admits in the ordinary `map_extra` proof module makes the functions look like verified reusable lemmas and lets any downstream proof assume their generic guarantees, including the new RCU invariant proofs that call them.
- **Suggestion:** Prove both lemmas from `value_filter`/`project_first_key` definitions and existing finite-map lemmas. If a proof is temporarily impossible, do not expose these as ordinary verified lemmas: move the minimum necessary assumption to the repository's explicit external/trusted boundary, narrow its signature as far as possible, and document the trust debt and removal plan.

## Medium

None.

## Low

None.

## Evidence check record

- Read all 910 lines of `diff.patch` and inspected the captured before/after implementations of `vstd_extra/src/map_extra.rs` and `lock-protocol/src/spec/utils.rs`.
- Searched added lines for `admit`, `assume`, `external_body`, `rlimit`, `requires`, and `ensures`. The only newly added trust primitives are `admit()` at after-image lines 452 and 462. No changed `#[verifier::rlimit(...)]` was present, so the `> 200` workflow check was not triggered; no `std`/`core`/`alloc` external specification was added or materially changed.
- Checked scope against the patch: admits visible in `tree_refines_atomic.rs` are unchanged context, so they were not reported as newly introduced findings.
- Static refutation attempt: the after image confirms both functions remain `pub`, generic over `K1`, `K2`, and `V`, and contain no proof steps before `admit()`. This supports, rather than refutes, the trust-surface finding.
- Per request, this was a fast, non-exhaustive review. No repository history, subagents, exhaustive rule enumeration, caller experiments, Verus execution, compilation, or CI verification was performed; therefore this report does not claim verification success or comprehensive defect coverage.
