# Review: `diff.patch` (isolated before/after snapshot)

> Produced from the VOSTD coding-guideline review criteria and the skill's API-contract criteria.
> Scope: fast, non-exhaustive static review of `diff.patch`, limited to the supplied `before/` and `after/` trees for `verified_libs/vstd_extra/src/ghost_tree.rs`.

**Bottom line:** No strong evidence-backed findings were identified. The change removes a trusted `axiom` by constructing the tracked child sequence and calling the existing exact constructor; the newly added preconditions are the facts required by `TreeNode::inv()` for that exact result. The visible callers use `EntryOwner`, whose `rel_children` predicate is `true` and whose `la_inv` restricts only node values, so the snapshot does not show a concrete caller-facing regression.

## High

None.

## Medium

None.

## Low

None.

## Evidence check record

- Reviewed the complete 43-line `diff.patch` and the surrounding before/after definitions of `TreeNodeValue`, `TreeNode::{new_val, tracked_new, inv_node, inv_children, inv}`, and all three visible `tracked_new_val` call sites.
- Trust/proof check: the former declaration was `pub axiom fn tracked_new_val`; the replacement is a checked `pub proof fn` that builds `Seq::new(N, |_| None)` using `Seq::tracked_empty` and `tracked_push`, then returns `Self::tracked_new(val, lv, children)`. This narrows rather than expands the trusted surface.
- Contract check: `val.la_inv(lv)` supplies `inv_node`'s level-aware value condition, and `forall|i: int| 0 <= i < N ==> val.rel_children(i, None)` supplies the `None` branch of `inv_children`; `val.inv()`, `lv < L`, and `N > 0` supply the remaining relevant invariant conjuncts. The exact `returns Self::new_val(val, lv)` guarantee is preserved.
- Caller check: the supplied snapshot has three uses of `tracked_new_val`. Their concrete value type is `EntryOwner`; its `rel_children` implementation returns `true`, and its `la_inv` is `self.is_node() ==> lv < L - 1`. No supplied call site demonstrates a newly excluded valid use.
- Maintainability/spec-reuse check: the helper is private, single-purpose, named for its tracked ownership role, and no equivalent helper appears in the supplied snapshot. No `#[verifier::rlimit(...)]` or external `std`/`core`/`alloc` specification is changed, so neither narrow workflow check is triggered.
- No verification was performed: per the requested fast-review constraints, this pass did not run Verus, experiments, history inspection, sub-agent personas, or an exhaustive guideline checklist. Consequently, the result establishes only that the supplied static evidence does not support a high-, medium-, or useful low-severity finding.
