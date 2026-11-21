# Review: PR #855 snapshot `diff.patch`

> Produced from the VOSTD coding-guideline criteria and the skill's API-contract criteria.
> Scope: the authoritative `pr-855-5c9e493bb78b/diff.patch`, with the supplied `before/` and `after/` trees used only for context.

**Bottom line:** The patch removes the visible `external_body` paging-layout axiom, but replaces it with the same build-specific facts in the contract of the generic `PagingConstsTrait`. An existing x86 IOMMU implementation has three levels while the build-selected x86 layout has four, so ordinary Rust can instantiate verified generic page-table code with a type that contradicts the proof contract. This hides rather than removes the trust boundary and should block the change until the build-specific facts are restricted to configurations that actually establish them.

## High

### The generic paging-constants contract is false for an existing implementation

- **Guidelines:** `centralize-trusted-boundaries`, `restrict-generic-trusted-models`, `api-preconditions`
- **Location:** `ostd/src/mm/mod.rs:162`
- **Evidence:** The patch adds these unconditional guarantees to `PagingConstsTrait::lemma_paging_consts_requirements` (and copies them into `lemma_paging_consts_properties`):

  ```rust
  Self::BASE_PAGE_SIZE() == PAGE_SIZE,
  Self::NR_LEVELS() == NR_LEVELS as PagingLevel,
  Self::BASE_PAGE_SIZE() / Self::PTE_SIZE() == NR_ENTRIES,
  ```

  On x86, the build-selected constant is `pub const NR_LEVELS: usize = 4` (`ostd/src/arch/x86/mm/mod.rs:51`), but the existing ordinary-Rust IOMMU implementation declares `const NR_LEVELS: PagingLevel = 3` (`ostd/src/arch/x86/iommu/dma_remapping/second_stage.rs:44-50`) and implements the same `PagingConstsTrait`. That implementation supplies no proof of the newly strengthened lemma. The diff simultaneously deletes the explicitly trusted `#[verifier::external_body] axiom_current_paging_consts_hardcoded`, whose documentation acknowledged that the restriction was trusted and not enforced by Verus.
- **Problem:** A generic trait law is available to every verified `C: PagingConstsTrait`, yet it is not a law of every executable implementation of that trait. Verified generic page-table proofs may therefore reason that the three-level IOMMU page table has the four-level build-selected layout. Moving an acknowledged assumption into a universally callable trait proof also makes the trust boundary substantially harder to audit.
- **Suggestion:** Keep `PagingConstsTrait::lemma_paging_consts_requirements` limited to facts that every implementation satisfies. Put the build-selected equalities behind a separate sealed/validated trait or an explicit model-validity predicate implemented only by the architecture paging constants, and require that narrower capability only in proofs that use global `PAGE_SIZE`, `NR_LEVELS`, or `NR_ENTRIES`. If the IOMMU configuration must participate in verified generic code, give it contracts stated in terms of its own associated constants rather than the CPU layout globals.

## Medium

No findings.

## Low

No findings.

## Evidence check record

- Read all 1,130 lines of the authoritative patch and inspected the supplied before/after context for the changed paging trait, architecture models, layout lemmas, and relevant implementations.
- Confirmed the contradictory values directly in the after tree: x86 `NR_LEVELS = 4` and IOMMU `PagingConsts::NR_LEVELS = 3`.
- Confirmed that the patch removes the explicit `external_body` layout axiom while adding the same layout equalities to the generic trait's required and derived proof contracts.
- No `#[verifier::rlimit(...)]` change and no new or materially changed `std`, `core`, or `alloc` external specification appears in the patch.
- Per the requested fast-review override, no history inspection, exhaustive rule enumeration, Verus run, CI verification, caller experiment, or modified-client experiment was performed. The finding is based on static source evidence; verification status is therefore unconfirmed.
