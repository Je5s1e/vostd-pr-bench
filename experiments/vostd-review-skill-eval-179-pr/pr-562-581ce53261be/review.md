# Review: `diff.patch`

> Produced from the VOSTD coding guidelines and API-contract criteria.
> Scope: the changes in `diff.patch`, with before/after context from `ostd/src/mm/kspace/kvirt_area.rs` and directly referenced page-table definitions and call sites.
> Fast-review limitation: no Verus verification, history analysis, caller experiment, or exhaustive rule-by-rule pass was performed.

**Bottom line:** The change usefully replaces a trusted axiom with an implemented proof, and static inspection found no high- or medium-severity contract, invariant, or trust-boundary defect. One low-severity naming issue remains: the implemented lemma still advertises itself as an axiom, obscuring the trust reduction that this patch achieves.

## High

None.

## Medium

None.

## Low

| Finding | Guideline | Detail |
| --- | --- | --- |
| Rename the proved fact as a lemma | `name-proof-roles` | At `ostd/src/mm/kspace/kvirt_area.rs:263`, the changed declaration is `pub proof fn axiom_kernel_range_valid(...)`, while its body at lines 272–282 proves the result. The guideline reserves `axiom_` for axioms and requires proved reusable facts to use `lemma_`. Rename it to `lemma_kernel_range_valid` and update its three call sites (lines 479, 682, and 1181). This makes the removal of a trust boundary visible to readers and searches. |

## Evidence check record

- Static diff check: read all 54 lines of `diff.patch` and compared the complete changed hunk against both supplied versions of `ostd/src/mm/kspace/kvirt_area.rs`.
- Proof-shape check: the new body calls `lemma_vaddr_range_bounds_spec_kernel`, establishes the numeric kernel bounds, derives `r.end > 0`, and proves the final inclusive upper bound used by `is_valid_range_spec`.
- Caller check: inspected all three after-tree call sites. The page-sized query range and the untracked-frame range are nonempty at their calls; `map_frames` now guards the call with `cursor_range.start < cursor_range.end`, matching the new precondition.
- Contract check: the helper's `requires` clauses restate the antecedent of the former implication, and its unconditional `ensures` exposes the same useful conclusion to legal callers. No missing caller-visible output or unsupported invariant was found statically.
- Trust and reuse check: the patch removes one `axiom fn` and introduces no `assume`, `admit`, `external_body`, uninterpreted fact, external standard-library specification, or duplicate range-bound lemma. It reuses the existing `lemma_vaddr_range_bounds_spec_kernel`.
- Workflow check: the patch contains no `#[verifier::rlimit(...)]` change, so no limit exceeds 200; it also adds no `std`, `core`, or `alloc` external specification.
- Verification disclosure: no Verus command, build, test, formatter, or isolated experiment was run. Conclusions are based only on static evidence in the supplied snapshot.
