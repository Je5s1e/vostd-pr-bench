# Review: `diff.patch` (`ostd/src/mm/dma/dma_coherent.rs`)

> Fast, non-exhaustive review of the supplied patch and its before/after context.
> Scope: `pr-856-619ad58877f8/diff.patch`; changed lines in `ostd/src/mm/dma/dma_coherent.rs` only.

**Bottom line:** No high- or medium-severity issue was found. The patch replaces the loop's trusted `assume` with a loop invariant and an existing multiplication lemma; the relevant bound is already required by `check_and_insert_dma_mapping`, which is called immediately before the loop. One low-severity import-layout issue remains.

## High

None.

## Medium

None.

## Low

| Finding | Guideline | Detail |
|---|---|---|
| Keep the new `vstd` proof import in the existing crate-level import. | `group-imports-by-crate` | At `ostd/src/mm/dma/dma_coherent.rs:2-3`, the patch adds `use vstd::arithmetic::mul::lemma_mul_inequality;` directly above the existing `use vstd::prelude::*;`. The guideline asks definitions from the same crate and import group to share one `use` statement. Prefer `use vstd::{arithmetic::mul::lemma_mul_inequality, prelude::*};` (leaving the separately `#[cfg]`-gated import alone). |

## Evidence check record

- Read the complete supplied `diff.patch` and the surrounding constructor in both `before/ostd/src/mm/dma/dma_coherent.rs` and `after/ostd/src/mm/dma/dma_coherent.rs`.
- Checked the cited source of the new invariant: `after/ostd/src/mm/dma/mod.rs:107-111` gives `check_and_insert_dma_mapping` the precondition `start_paddr + num_pages * crate::mm::PAGE_SIZE <= usize::MAX`; the call at `dma_coherent.rs:127` precedes the loop, and the loop invariant preserves the same bound at lines 159-168.
- Checked the local proof chain: `i < frame_count` at line 169 supplies the multiplicand ordering used by `lemma_mul_inequality` at line 173, while the preserved whole-segment bound supplies the final address limit for line 175. No new `assume`, external specification, or `#[verifier::rlimit(...)]` is introduced.
- The target snapshot does not contain the guideline pages or vendored `vstd` lemma definition. The rule name and wording for the low finding were cross-checked against the workspace's available VOSTD maintainability guideline copy; no claim here depends on an uninspected lemma signature.
- **No verification disclosure:** Per the requested fast-review constraints, no Verus build, CI run, caller experiment, or other executable verification was performed. Conclusions are static and non-exhaustive.
