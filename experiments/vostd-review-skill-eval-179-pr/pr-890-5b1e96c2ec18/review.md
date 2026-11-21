# Review: PR 890 snapshot `5b1e96c2ec18`

> Produced from the supplied `diff.patch`, with `before/` and `after/` used only for line-numbered context.
> Scope: two changed files: `ostd/src/task/scheduler/info.rs` and `ostd/src/util/ops.rs`. This fast review covers maintainability, proof/trust assumptions, API contracts and invariants, `rlimit > 200`, and spec reuse.

**Bottom line:** The new `lemma_filter_laws` does not have a parameter named `iter`, but its contract and body reference `iter`, while its only call supplies `iter` as a third argument. This is a direct compile/verification blocker in the changed code. The other contract change usefully makes the iterator-law guarantee unconditional, and the new `set_if_is_none` equivalence closes the success/failure result contract without exposing an evident invariant gap.

## High

### `lemma_filter_laws` has an inconsistent signature and call

- **Guideline:** `preserve-exec-code` / proof-engineering correctness
- **Location:** `ostd/src/util/ops.rs:141` and `ostd/src/util/ops.rs:148`
- **Evidence:** The call is `lemma_filter_laws(iter, pred, ret);`, but the added signature declares only `pred: P` and `ret: core::iter::Filter<I, P>`. Its `requires` and body nevertheless use the undeclared name `iter`:

  ```rust
  proof fn lemma_filter_laws<I: Iterator, P: FnMut(&I::Item) -> bool>(
      pred: P,
      ret: core::iter::Filter<I, P>,
  )
      requires
          iter.obeys_prophetic_iter_laws(),
          filter_post(iter, pred, ret),
  {
      filter_postcondition(iter, pred, ret);
  }
  ```

  Thus the helper both references an unbound value and is called with the wrong arity.
- **Problem:** The changed module cannot compile/verify as written, so the strengthened `range_difference` postcondition is not established by this patch.
- **Suggestion:** Prefer removing this single-use wrapper and proving the iterator-law fact directly in the existing assertion block. If a named helper is genuinely required for instantiation, add `iter: I` as its first parameter (matching the existing call) and keep it local to `range_difference` if Verus permits, consistent with `inline-single-use-proof-helpers`.

## Medium

No medium-severity findings.

## Low

No low-severity findings.

## Evidence check record

- Read all 63 lines of the supplied `diff.patch`; treated it as the authoritative change set.
- Checked the complete `before/` and `after/` context for both changed files and searched all supplied snapshots for `lemma_filter_laws`. It has exactly one call, introduced by this patch, and no prior definition.
- API-contract check: `AtomicCpuId::set_if_is_none` now states `ret is Ok <==> old(perm).view().value == Self::NONE`; the existing success and error clauses preserve the permission value appropriately. No high- or medium-confidence contract defect was found there.
- Iterator-contract check: changing `ret.obeys_prophetic_iter_laws() && P ==> Q` to separate guarantees `ret.obeys_prophetic_iter_laws(), P ==> Q` intentionally strengthens the API and avoids making the iterator laws conditional. The blocker is the malformed proof helper used to establish that guarantee, not the guarantee itself.
- Assumption/trust check: the patch adds no `assume`, `admit`, `external_body`, or external specification.
- Workflow check: the only visible verifier limit is the unchanged `rlimit(50)`, below 200. No `std`, `core`, or `alloc` external specification is added or materially changed.
- Spec-reuse check: the patch reuses `filter_postcondition`; no duplicate public spec model was introduced. The private wrapper is single-use and should be inlined or scoped locally as noted above.
- **No-verification disclosure:** Per the fast-review instruction, no Verus run, build, tests, caller experiment, Git history analysis, sub-agent review, or exhaustive guideline pass was performed. Findings are based solely on static inspection of `diff.patch` plus the supplied before/after context.
