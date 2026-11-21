# Review: PR #710 snapshot `81e3abfc0815`

> Produced from the VOSTD maintainability/proof-engineering guidance and API-contract criteria.
> Scope: fast, non-exhaustive static review of `diff.patch`, with `before/` and `after/` used only for surrounding context. No history, Verus run, caller experiment, or exhaustive checklist was performed.

**Bottom line:** The change improves the architecture model, but it introduces an unsound generic trust boundary: every implementation of `PagingConstsTrait` can now obtain x86-specific constant equalities from an `external_body`. Because the trait is public and is deliberately used by generic page-table code, this can make the verifier accept those equalities for configurations that do not satisfy them. This should block merging until the trusted assumption is removed or restricted to the concrete build-selected paging configuration.

## High

### The generic paging trait grants architecture-specific facts to arbitrary implementations

- **Guidelines:** `restrict-generic-trusted-models`, `centralize-trusted-boundaries`
- **Location:** `ostd/src/mm/mod.rs:221`
- **Evidence:** The new default trait method is trusted rather than proved:

  ```rust
  #[verifier::external_body]
  proof fn axiom_current_paging_consts_hardcoded()
      ensures
          Self::BASE_PAGE_SIZE() == PAGE_SIZE,
          Self::NR_LEVELS() == NR_LEVELS as PagingLevel,
          Self::BASE_PAGE_SIZE() / Self::PTE_SIZE() == NR_ENTRIES,
  ```

  Yet `PagingConstsTrait` is public (`ostd/src/mm/mod.rs:78`) and its actual requirements at lines 155–167 do not require any of those three equalities. The diff then calls this axiom in generic code, including `lock_range<C: PageTableConfig>` (`ostd/src/mm/page_table/cursor/locking.rs:109`) and `dfs_get_idx_range<C: PagingConstsTrait>` (`ostd/src/mm/page_table/cursor/locking.rs:754`), with many more calls across generic cursor and ownership proofs. The repository context also contains non-current paging configurations; for example, the x86 IOMMU paging constants declare three levels (`ostd/src/arch/x86/iommu/dma_remapping/second_stage.rs:44-50`), while the build-selected x86 constant is four (`ostd/src/arch/x86/mm/mod.rs:50-51`).
- **Problem:** `external_body` makes the postconditions available for any `Self`, without a predicate or bound tying `Self` to the current architecture. A legal different implementation can therefore receive false equalities, so downstream generic proofs are only conditionally valid even though their APIs expose no such condition. The TODO documents the debt but does not constrain the verifier or callers.
- **Suggestion:** Remove the default trusted method. Prove these equalities on the concrete build-selected `PagingConsts` implementation and invoke that concrete lemma only in non-generic current-architecture code; generic proofs should instead use `C::BASE_PAGE_SIZE()`, `C::NR_LEVELS()`, and the derived entry count. If a temporary bridge is unavoidable, require a sealed/model-validity predicate or marker implemented only for reviewed configurations, and place the narrowly scoped trust declaration in the repository's centralized external/trust-boundary layer.

## Medium

No strong medium-severity findings in this fast review.

## Low

No useful low-severity findings in this fast review.

## Evidence check record

- Reviewed the supplied `diff.patch` with targeted inspection of all changed paths, trust markers, contracts, rlimits, and the corresponding `before/` and `after/` context for the architecture and paging-model APIs.
- Searched the after-tree for `assume`, `admit`, `axiom`, `external_body`, changed contracts/invariants, and `#[verifier::rlimit]`. The new `axiom_current_paging_consts_hardcoded` is called throughout generic proofs; the only added rlimit found is `20`, below the workflow cap of `200`.
- Checked the trait requirements, the concrete x86 paging implementation, representative generic call sites, and an existing paging configuration whose level count differs from the hardcoded current x86 value.
- The new architecture lemmas factor existing x86 conversion properties into reusable generic helpers; this fast pass found no stronger specification-reuse issue and no newly added or materially changed `std`/`core`/`alloc` external specification.
- **No-verification disclosure:** Per the requested fast-review override, no Verus verification, build, test, isolated caller experiment, history review, sub-agent pass, or exhaustive guideline audit was performed. Findings are based on static source evidence only.
