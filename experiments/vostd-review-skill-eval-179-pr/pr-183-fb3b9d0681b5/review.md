# Review: PR #183 snapshot `fb3b9d0681b5` (`diff.patch`)

> Produced from the supplied patch and before/after snapshots using the VOSTD maintainability, proof-engineering, API-contract, invariant, rlimit, and specification-reuse criteria.
> Scope: `pr-183-fb3b9d0681b5/diff.patch`; changed code in `lock-protocol/src/mm/page_table/{mod.rs,cursor/mod.rs}`, compared against the corresponding `before/` and `after/` files.

**Bottom line:** The snapshot should not merge as verified code. It makes `Cursor::move_forward` depend on two new trusted facts: one reusable lemma has had its proof replaced by `admit()`, and the remaining carry argument is asserted with a local quantified `assume`. These are independent obligations and each can establish `self.wf(spt)` without a checked derivation. The patch also adds about eighty lines of private sequence-model proof machinery with no caller in the captured tree.

## High

### H1 — A previously proved alignment lemma is now admitted

- **Guideline:** `centralize-trusted-boundaries`
- **Location:** `lock-protocol/src/mm/page_table/mod.rs:829`
- **Evidence:** The changed lemma promises
  ```rust
  forall|l: PagingLevel|
      level <= l <= C::NR_LEVELS_SPEC() ==> pte_index::<C>(x, l) ==
          pte_index::<C>(align_down(x, page_size::<C>(level)), l)
  ```
  but its entire body at line 839 is `admit();`. In the before snapshot, this lemma had an explicit proof body; the patch deletes that body and leaves it commented out. The lemma is then invoked at `cursor/mod.rs:324` to prove the higher-level index equalities needed for `assert(self.wf(spt))` at line 327.
- **Problem:** This is a direct expansion of the trusted computing base at a reusable proof boundary. Verus can accept the cursor invariant from the lemma's unchecked postcondition, so verification of `move_forward` no longer establishes the alignment fact it relies on.
- **Suggestion:** Restore a checked proof of the strengthened postcondition. In particular, prove that alignment to `page_size::<C>(level)` preserves every index at `l >= level`, using the page-size/shift relationship; do not retain the old proof as commented code or replace it with another assumption.

### H2 — `move_forward` assumes the core carry-preservation fact

- **Guideline:** `centralize-trusted-boundaries`
- **Location:** `lock-protocol/src/mm/page_table/cursor/mod.rs:315`
- **Evidence:** The new proof contains
  ```rust
  assume(forall|i: u8|
      self.level < i <= self.guard_level ==>
      pte_index::<C>(aligned_va, i) == pte_index::<C>(next_va, i));
  ```
  and immediately consumes it at lines 319–325 to establish the higher-level index equality from which line 327 proves `self.wf(spt)`. The loop only supplies the concrete termination fact `pte_index::<C>(next_va, self.level) != 0` at line 307; the relationship between that fact and all higher indices is precisely what the assumption bypasses.
- **Problem:** The assumed quantified equality is the central arithmetic obligation of the cursor advance, not an environmental or hardware boundary. Keeping it beside the caller lets an unchecked fact certify the postcondition of `move_forward`, and its comment (`// No overflow.`) justifies a different assertion rather than this assumption.
- **Suggestion:** Replace the assumption with a proved carry-termination lemma: from alignment, the page-size increment, and the nonzero index at the terminating level, derive that indices strictly above that level do not change, then invoke that lemma here.

## Medium

### M1 — The new sequence model and injectivity proof have no consumer

- **Guideline:** `avoid-unused-spec-helpers`
- **Location:** `lock-protocol/src/mm/page_table/mod.rs:642`
- **Evidence:** The patch adds `is_valid_pte_index_seq`, `pte_index_seq_to_nat`, and the 62-line `lemma_pte_index_seq_to_nat_injective` at lines 642–720. A search of every Rust file in the captured `after/` tree finds these names only in their definitions and in the lemma's own recursive body; neither changed cursor proof calls them.
- **Problem:** This adds a parallel radix/sequence model and a substantial proof that contributes to no current contract or proof obligation, increasing the surface reviewers and future maintainers must understand without reducing either trusted gap above.
- **Suggestion:** Remove these three helpers and the now-unneeded `Seq` import. Reintroduce them with the proof that actually consumes them if they become necessary.

## Low

No low-severity findings.

## Evidence check record

- Read the complete 321-line `diff.patch` and the relevant line-numbered regions in both supplied before/after snapshots.
- Confirmed H1 is a regression in the scoped diff: the before snapshot contains a proof body for `lemma_aligned_pte_index_unchanged`; the after snapshot replaces it with `admit()` while changing the guaranteed alignment level. Confirmed its result is consumed by `move_forward`.
- Confirmed H2 is introduced by the scoped diff and is distinct from H1: it relates `aligned_va` to `next_va` after page-size addition, whereas H1 relates `old(self).va` to its aligned address.
- Confirmed M1 with a tree-wide static name search in the supplied `after/` snapshot; all matches are definitions, internal calls, or the lemma's recursion.
- No changed `#[verifier::rlimit(...)]` was present, so the `> 200` workflow check did not trigger. No new or materially changed external specification for a `std`, `core`, or `alloc` API was present.
- The change to `pte_index_add_with_carry` removes its recommendation and defines the formerly out-of-domain `cur_level < add_level` case explicitly; static inspection found no concrete API-precondition or API-postcondition defect to report from that change.
- Per the fast-review instruction, no Git history, Verus execution, exhaustive guideline checklist, caller experiment, or other dynamic verification was performed. Findings are based only on the supplied patch and snapshots; this review does **not** claim that the proposed corrections have been verified by Verus.
