# Review: PR #634 snapshot 64d2718d5a4d

> Produced from the VOSTD coding-guideline review criteria and API-contract criteria.
> Scope: fast, non-exhaustive static review of `diff.patch` (5 files, 57 insertions, 14 deletions), with the corresponding `before/` and `after/` source used for context.

**Bottom line:** No strong evidence-backed high-, medium-, or useful low-severity issue was found in the scoped change. The patch replaces three axioms with proof implementations, factors tree-node destruction into a reusable tracked helper, and strengthens the untracked-frame constructor preconditions consistently with its checked caller context. This conclusion is limited to static inspection and is not a verification result.

## High

None.

## Medium

None.

## Low

None.

## Evidence check record

- Inspected every hunk in `diff.patch` and the surrounding `before/` and `after/` definitions and callers.
- Checked the recursive `segment_drop_embedded` implementation at `ostd/specs/mm/embedding/segment.rs:148` against the preconditions and frame-preservation guarantees of `frame_drop_embedded`. The range alignment, strict non-emptiness, upper bound, region invariant, and per-slot conditions supply the first call and recursively preserve the tail call's obligations.
- Checked `CursorContinuation::tracked_new` and `CursorOwner::tracked_new` at `ostd/specs/mm/page_table/cursor/owners.rs:176` and `:2623` against their `new` specifications. The added `TreeNode::tracked_into_parts` contract at `verified_libs/vstd_extra/src/ghost_tree.rs:435` pins both returned tracked components to the consumed node's value and children.
- Checked the changed `new_untracked_frame` requirements at `ostd/specs/mm/page_table/node/entry_owners.rs:267` against its visible caller at `ostd/src/mm/kspace/kvirt_area.rs:1020`; the caller context tracks the level bound, physical alignment, and end-address bound needed by the strengthened contract.
- Checked the removed `guard_ref` ghost input from the `dfs_acquire_lock` specification and call at `ostd/src/mm/page_table/cursor/locking.rs:199` and `:518`. It was not referenced by the callee contract, while the retained `entry_own`, guard ledger, and region parameters carry the stated ownership and preservation obligations.
- No added or changed `#[verifier::rlimit(...)]` was present, so the `rlimit > 200` check did not trigger. No new or materially changed external specification for a `std`, `core`, or `alloc` API was present, so the upstream-spec check did not trigger.
- No duplicated specification or proof helper with equivalent semantics was identified in the scoped `after/` tree; the new `tracked_into_parts` helper is the operation used to eliminate the two constructor axioms.
- Per the requested fast-review constraints, this review did not inspect Git history, spawn persona reviewers, enumerate every guideline rule, run Verus, execute caller experiments, or perform exhaustive repository-wide searches. CI/Verus verification was not run and no proof-verification claim is made.
