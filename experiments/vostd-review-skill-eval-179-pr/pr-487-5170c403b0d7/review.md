# Review: PR #487 snapshot `5170c403b0d7`

> Produced from the VOSTD coding-guideline criteria and the skill's API-contract criteria.
> Scope: `pr-487-5170c403b0d7/diff.patch` is authoritative, with `before/` and `after/` used for line-numbered context. No branch or commit SHA metadata was supplied.

**Bottom line:** The new weak-memory RCU reader still makes its safe public reference-returning APIs depend on an `external_body` helper that fabricates the pointee permission; the module itself acknowledges that the traversal argument needed to justify this reference has not been completed. That trust hole should block treating the new reader as verified. Before merge, the generic core-atomic specifications should also be moved to the reusable specification library, and the newly added uncompiled copy of the old RCU implementation should be removed.

## High

### Safe RCU reads manufacture the permission needed to return a shared reference

- **Guidelines:** `centralize-trusted-boundaries`, `complete-external-contracts`, `api-postconditions`
- **Location:** `ostd/src/sync/rcu/mod.rs:746`
- **Evidence:** The helper used by both reader paths is trusted and creates its required authority from nothing:

  ```rust
  #[verifier::external_body]
  unsafe fn assume_shared_ref<'a, P: NonNullPtrRef<'a>>(ptr: NonNull<P::Target>) -> P::Ref {
      proof_decl! {
          let tracked perm: P::RefPermission = Tracked::<P::RefPermission>::assume_new().get();
      }
      unsafe { P::raw_as_ref(ptr, Tracked(perm)) }
  }
  ```

  `RcuInner::read_with` calls it directly at lines 571-590, and `RcuReadGuardInner::get` calls it at lines 601-602. The public `RcuOption::read_with` exposes the result at lines 875-895. The new module documentation also states that the loaded root's `BlockInfo` is not installed in the protection map and that “`assume_shared_ref` still stands in for the final traversal argument that grants the client pointer's reference permission” (`ostd/src/sync/rcu/mod.rs:106-115`).
- **Problem:** The public reader can return `P::Ref` without a checked link from the observed allocation and live RCU guard to `P::RefPermission`. All downstream reasoning about the returned reference therefore rests on a locally fabricated linear permission, so the new weak-memory history and guard tokens do not establish the API's central safety postcondition.
- **Suggestion:** Complete the protection-map/traversal step so the acquire load's exact `BlockInfo` and live `RcuReadGuardToken` derive the matching `P::RefPermission`, pass that permission into `P::raw_as_ref`, and remove `assume_shared_ref`. Until then, keep the reference-returning API outside the claimed verified surface rather than discharging it with `external_body`.

## Medium

### Move the generic core-atomic weak-memory specifications into the reusable library

- **Guideline:** `upstream-reusable-specs`
- **Location:** `ostd/specs/sync/weak_memory.rs:1454`
- **Evidence:** The patch adds a 2,804-line generic weak-memory framework under the OSTD-specific spec tree. For example, `AtomicUsizeW` is documented as a “TCB wrapper around Rust's `AtomicUsize`” and provides external contracts for `new`, relaxed/acquire loads, CAS, and stores (`ostd/specs/sync/weak_memory.rs:1454-1669`). The same file generates wrappers for multiple integer atomics and separately defines generic `AtomicBoolW` and `AtomicPtrW<T>` wrappers. These contracts model `core::sync::atomic` operations and contain no RCU- or OSTD-specific type dependency.
- **Problem:** These are materially new external specifications for reusable `core` atomic APIs. Keeping them in `ostd/specs/sync` makes other verified components duplicate this trusted model and prevents a single shared review of its assumptions.
- **Suggestion:** Move the generic history/view model and atomic wrappers to `verified_libs/vstd_extra` (or propose them to upstream vstd), then keep only the RCU-specific invariant composition in OSTD.

### Do not add an uncompiled 1,128-line implementation snapshot as source-level reference material

- **Guidelines:** `avoid-unused-spec-helpers`, `document-real-proof-debt`
- **Location:** `ostd/src/sync/rcu/__mod.rs:1`
- **Evidence:** The patch adds `ostd/src/sync/rcu/__mod.rs` as a new 1,128-line file, while the compiled module says, “The previous SC proof-oriented implementation is kept in `__mod.rs` as reference and is not compiled” (`ostd/src/sync/rcu/mod.rs:4-6`). The copy contains complete unused executable/proof machinery and admissions, including `assume(perm.not_empty())` and `assume(1 < perm.frac())` at lines 389-390 and four `assume(false)` branches at lines 598, 601, 687, and 706.
- **Problem:** This permanently checks in a second, dead RCU implementation that cannot be type-checked or kept synchronized with the live API. Calling it “reference” does not identify a current proof obligation; it makes searches for trust constructs noisy and leaves future maintainers to distinguish obsolete proof code from the compiled model.
- **Suggestion:** Remove `__mod.rs` and rely on version control for the old implementation. If a small part is still needed to guide a concrete follow-up, retain only that minimal lemma/model in a compiled or test-checked location with a precise TODO naming the remaining obligation.

## Low

No useful low-severity findings.

## Evidence check record

- Read the authoritative 12,913-line `diff.patch` and used the supplied `after/` files for source line numbers and surrounding contracts; consulted `before/` to confirm the reader and weak-memory implementation are materially rewritten by this patch.
- Traced `assume_shared_ref` through `RcuInner::read_with`, `RcuReadGuardInner::get`, and the public `RcuOption::read_with` wrapper. The patch's own module documentation confirms that the permission-producing traversal argument is unfinished, so static refutation did not find an existing checked source for `P::RefPermission`.
- Inspected the generic `AtomicUsizeW`, macro-generated integer wrappers, `AtomicBoolW`, and `AtomicPtrW<T>` boundaries. They specify `core::sync::atomic` behavior independently of RCU, triggering the narrow `upstream-reusable-specs` workflow check.
- Confirmed that `__mod.rs` is newly added, is not declared as a Rust module, and is explicitly described by the compiled module as uncompiled reference material. Its admissions are not reported as independent proof failures because the file is not compiled; they support the maintainability finding only.
- No added or changed `#[verifier::rlimit(...)]` appears in `diff.patch`, so the workflow `> 200` check did not trigger.
- **No-verification disclosure:** Per the fast-review override, no Git history inspection, Verus invocation, build, CI run, isolated caller experiment, exhaustive guideline checklist, or sub-agent pass was performed. Findings are based solely on static inspection of the authoritative patch and supplied before/after context.
