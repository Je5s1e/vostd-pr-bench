# Review: PR 802 isolated snapshot `2d0e9d0e7c27`

> Produced from the supplied `diff.patch` and its captured `before/` and `after/` trees, using the VOSTD maintainability, proof-engineering, API-contract, and narrowly triggered workflow criteria.
> Scope: fast, non-exhaustive review of `pr-802-2d0e9d0e7c27/diff.patch`; no repository history, sub-reviewers, Verus execution, caller experiments, or exhaustive checklist pass.

**Bottom line:** The verified `EarlyFrameAllocator::alloc` contract carries enough old/final tail state to reason about sequential allocations, but the newly trusted global `early_alloc` wrapper erases that state. Consequently its callers cannot prove the cross-call non-overlap property that its documentation says is trusted and provided by the inner allocator. The remaining findings are readiness issues: one axiom has no consumer, and the new general-purpose `core::alloc::Layout` external specification should be proposed at the upstream reusable layer.

## High

None.

## Medium

### The global allocation API cannot express cross-call non-overlap

- **Guideline:** `api-postconditions`
- **Location:** `ostd/src/mm/frame/allocator.rs:566`
- **Evidence:** The new documentation says that “the cross-call progression (distinct allocations never overlap) is trusted — it is provided by [`EarlyFrameAllocator::alloc`]” (lines 555–558). However, the wrapper's entire formal result contract at lines 567–577 only says that a successful address is aligned and contained in one fixed modeled region:

  ```rust
  #[verus_spec(ret =>
      ensures
          ret matches Some(pa) ==> {
              &&& pa as int % alloc_align(layout) == 0
              &&& (early_allocator_region_1().start <= pa
                  && pa + alloc_size(layout) <= early_allocator_region_1().end
                  || early_allocator_region_2().start <= pa
                      && pa + alloc_size(layout) <= early_allocator_region_2().end)
          },
          ret is None ==> true,
  )]
  ```

  By contrast, the inner `alloc` contract exposes `old(self)` and `final(self)` bump tails (lines 415–432), which is the information from which sequential separation can be derived. That state is not present in `early_alloc`'s API, so two legal calls may each satisfy the wrapper contract while returning the same nonempty range. The runtime implementation may still advance the mutex-protected allocator, but verified callers cannot use that fact.
- **Suggestion:** Give the global wrapper a stateful specification that exposes allocation progression—for example, a ghost model/token for the global allocator whose old/final tails or allocated set is updated by each call—and ensure that a successful result is disjoint from the old allocated set. If that property is intentionally outside the verified API, remove the claim that the contract supplies cross-call non-overlap and explicitly delimit which clients remain trusted.

## Low

| Finding | Guideline | Detail |
|---|---|---|
| `axiom_early_regions_wf` has no consumer | `avoid-unused-spec-helpers` | `ostd/src/mm/frame/allocator.rs:334` adds `pub(crate) axiom fn axiom_early_regions_wf()`, but a full search of the captured `after/` tree finds only its definition. Remove it until a proof needs it, or use it at the abstraction boundary that requires these region bounds. |
| General `Layout` specs belong upstream | `upstream-reusable-specs` | `verified_libs/vstd_extra/src/external/layout.rs:7-43` introduces an external type specification, an axiom for `Layout` validity, and assumed specifications for the standard `core::alloc::Layout::{size, align}` APIs. These are general `core` contracts rather than OSTD-specific models; propose them to upstream Verus/vstd (and track that proposal) so projects do not accumulate competing trusted models. |

## Evidence check record

- Read all 426 lines of the supplied `diff.patch` and inspected the cited `before/` and `after/` source context.
- Searched the full captured `after/` tree for every new early-allocation model/helper and for other `Layout` external specifications. `axiom_early_regions_wf` has no call site; the other new allocator models are referenced by contracts or proofs.
- Compared the pre-change allocation loop with the unrolled post-change executable code. The patch preserves the original loop in an adjacent `Origin Rust` block and the two attempts retain their order, conditions, and writes; no executable-semantics finding is reported.
- No `#[verifier::rlimit(...)]` change appears in the patch, so the numeric rlimit check was not triggered.
- The workflow upstream-reuse check was triggered by the newly added external specifications for `core::alloc::Layout`.
- **No-verification disclosure:** Per the requested fast-review constraints, no Verus command, build, test, isolated caller experiment, repository-history inspection, or exhaustive guideline checklist was run. Findings are based on static evidence from the supplied snapshot only.
