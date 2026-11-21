# Review: PR #171 snapshot (`diff.patch`)

> Produced from the VOSTD coding-guideline criteria available to this review.
> Scope: fast, non-exhaustive static review of the immutable `diff.patch` and its `before/` and `after/` context in `pr-171-6cc1b7bbb99b`; no history, subagent passes, Verus runs, or proof experiments were performed.

**Bottom line:** The change is not ready to merge. The new `inv_stray_in_node` invariant is directly contradicted by both deallocation transitions, which deliberately retain a `true` stray after removing its node. Separately, the new allocation proof introduces an explicit `admit()` at the exact point where the updated stray-count invariant must be established.

## High

### The new stray invariant is false after deallocation

- **Guideline:** `implement-inv-for-models`
- **Location:** `lock-protocol/src/spec/rcu/tree.rs:173`
- **Evidence:** The new invariant says `self.strays.contains_key((nid, paddr)) ==> self.nodes.contains_key(nid)` (`tree.rs:173-179`). However, `protocol_deallocate` removes the node and then replaces the false stray with a true stray: `remove nodes -= [ nid => NodeState::Locked ];` followed by `remove strays -= [ (nid, paddr) => false ]; add strays += [ (nid, paddr) => true ];` (`tree.rs:342-350`). `normal_deallocate` performs the same state change (`tree.rs:398-406`).
- **Problem:** A legal deallocation post-state contains `(nid, paddr)` in `strays` while `nid` is absent from `nodes`, so it violates the newly declared invariant. Existing admitted inductiveness proofs can hide this contradiction, but cannot make the modeled transition preserve the invariant.
- **Suggestion:** Align the invariant with the intended meaning of the boolean. If only live/false strays require a node, guard the implication with `self.strays[(nid, paddr)] == false`; otherwise change both deallocation transitions to remove the stray entry rather than retain it as `true`. Then discharge the affected inductiveness proofs without admits.

### The allocation invariant proof is trusted locally

- **Guideline:** `centralize-trusted-boundaries`
- **Location:** `lock-protocol/src/spec/rcu/tree.rs:1228`
- **Evidence:** The newly added proof contains `assert(post.count_stray_false(node_id) == 1) by { // This is absolutely true, but I do not have enough time admit(); }` (`tree.rs:1228-1231`).
- **Problem:** This `admit()` is precisely the missing step used to establish `post.inv_stray_at_most_one_false_per_node()`. It therefore turns preservation of a state-machine invariant into an unchecked local assumption, and the time-pressure comment does not document a valid trusted boundary.
- **Suggestion:** Prove the singleton update explicitly: establish that the pre-state filtered submap for `nid` has no false value, characterize the post-state as insertion of `(nid, paddr) => false`, and use or add a reusable `value_filter`/map-insert cardinality lemma. Keep the proof in `vstd_extra` if the lemma is generally useful; do not retain the `admit()` in the inductiveness proof.

## Medium

No evidence-backed medium-severity findings in this fast review.

## Low

No useful low-severity findings in this fast review.

## Evidence check record

- Read all 282 lines of `diff.patch` and inspected the corresponding changed regions in both `before/` and `after/` snapshots.
- Refutation check for the invariant finding: both deallocation transitions remove `nodes[nid]` and retain `strays[(nid, paddr)]` with value `true`; the new invariant has no value guard. The contradiction is direct from the modeled updates.
- Refutation check for the trust finding: the `admit()` is newly introduced by the patch and sits inside the proof of the changed stray-count invariant.
- The changed `lemma_value_filter_choose` and new `left_submap` helper were inspected statically; this fast pass found no sufficiently strong contract or obvious-reuse defect to report.
- No added or changed `#[verifier::rlimit(...)]` was present, so the `> 200` workflow check was not triggered. No external specification for a `std`, `core`, or `alloc` API was added or materially changed.
- **Verification disclosure:** Per the requested fast-review constraints, no Verus invocation, compilation, CI run, targeted client, standalone proof experiment, repository history search, or exhaustive guideline sweep was performed. Findings above rely only on the captured patch and before/after source evidence.
