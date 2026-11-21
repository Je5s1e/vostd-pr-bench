# Review: PR #136 — Prove remaining admits in rw

> Fast, non-exhaustive static review of `diff.patch` (authoritative), with `before/` and `after/` used only for line numbers and surrounding context. No Verus build, proof verification, caller experiment, history review, or exhaustive guideline pass was performed.
>
> Scope: `https://github.com/asterinas/vostd/pull/136`, base `a9baa185700f3059fae49218ba547551af9cf044`, head `3319ef543031d4ee017c3e445255051949139e26`; four changed files under `lock-protocol/src/exec/{rcu,rw}`.

**Bottom line:** The change adds three `admit()` calls to preserve a new loop invariant that feeds the public `lock_range` postcondition. Those calls make the proof accept the path relationship without establishing it, so the PR does not achieve its stated goal of proving the remaining admits and should not merge in this form. The new paging-offset range lemma is also introduced twice with identical contracts and proof bodies, creating avoidable proof duplication.

## High

### H1 — Three new admits trust the central path invariant

- **Guideline:** `centralize-trusted-boundaries`
- **Location:** `lock-protocol/src/exec/rw/cursor.rs:506`, `lock-protocol/src/exec/rw/cursor.rs:549`, `lock-protocol/src/exec/rw/cursor.rs:589`
- **Quoted evidence:** Each of the three loop branches adds the same proof block:

  ```rust
  assert(m.path().is_prefix_of(va_range_get_tree_path(*va))) by {
      admit();
  };
  ```

  The asserted fact is the new loop invariant at line 421 (and loop exit condition at line 445). `lock_range` publicly ensures `res.1@.path() =~= va_range_get_tree_path(*va)` at line 353.
- **Problem:** These local admits introduce trusted facts on all three branches that descend to the next page-table level. The prefix relationship is therefore assumed rather than proved while it is being carried toward the function's caller-visible exact-path guarantee; ordinary Verus success would not validate this reasoning.
- **Suggestion:** Prove one reusable step lemma showing that extending the model path with the current child preserves the prefix of `va_range_get_tree_path(*va)`, using the existing `cur_nid == va_level_to_nid(va.start, level)`, `lemma_va_level_to_nid_inc`, and the path-length/guard-level facts. Invoke that lemma in each branch and remove all three admits. The pre-existing admit later in the function at line 626 is outside this diff, but it must also be discharged before the function's postcondition is fully verified without trust.

## Medium

### M1 — The same new proof lemma is maintained in both protocol implementations

- **Guideline:** `reuse-existing-specifications`
- **Location:** `lock-protocol/src/exec/rw/common.rs:76`; duplicate at `lock-protocol/src/exec/rcu/common.rs:142`
- **Quoted evidence:** Both changed files introduce an identical public lemma:

  ```rust
  pub proof fn lemma_va_level_to_offset_range(va: Vaddr, level: PagingLevel)
      requires 1 <= level <= 4,
      ensures 0 <= va_level_to_offset(va, level) < 512,
  {
      let offset = va_level_to_offset(va, level);
      assert(offset < 512) by {
          assert(low_bits_mask(9) == 511) by {
              lemma_low_bits_mask_values();
          };
          assert((va >> (12 + (level - 1) as usize * 9)) & 511 <= 511) by (bit_vector);
      }
  }
  ```
- **Problem:** This is one paging-arithmetic fact with the same contract and proof, newly copied into two sibling implementations. Future changes can make the RCU and RW definitions or lemmas drift even though this fact is protocol-independent.
- **Suggestion:** Place the paging-address definition and range lemma in a shared lock-protocol helper/spec module and import it from both RCU and RW. If the duplicated `va_level_to_offset` definitions cannot yet be consolidated, centralize a generic bit-extraction range lemma and make both protocol-specific lemmas thin wrappers around it.

## Low

No strong low-severity findings were recorded in this fast review.

## Evidence check record

- Read all 366 lines of `diff.patch`; treated it as the only authority for change scope.
- Read the affected regions in all four `after/` files and compared the corresponding `before/` regions for context and stable line attribution.
- Searched the patch and changed snapshots for `admit`, `assume`, `external_body`, axioms, and `rlimit`. The patch adds exactly the three admits cited in H1; it adds no `assume`, `external_body`, or `#[verifier::rlimit(...)]` change. Existing trusted boundaries in surrounding snapshots were not independently reported because they were not introduced by this diff.
- Checked the trace rewrite algebraically at the source level: for sequence index `i`, the new definition selects paging level `4 - i`, matching the old recursion's order for levels satisfying `1 <= level <= 4`. No separate high- or medium-confidence trace-contract regression was identified statically.
- No new or materially changed external specification for a `std`, `core`, or `alloc` API appears in the patch, so the upstream-spec placement check was not triggered.
- No Verus invocation, build, CI rerun, isolated caller experiment, or proof experiment was performed. Findings are based on direct static evidence only and do not assert verification results.
