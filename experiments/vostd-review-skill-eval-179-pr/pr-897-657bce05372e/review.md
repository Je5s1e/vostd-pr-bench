# Review: PR 897 isolated patch

> Produced from the supplied `diff.patch`, its `before/` and `after/` snapshots, and the VOSTD review skill's proof-engineering and API-contract criteria.
> Scope: fast, non-exhaustive review of `diff.patch` in `/Users/chao/workspace/REvolve/vostd-pr-test/pr-897-657bce05372e`; no repository history, sub-reviewers, Verus runs, exhaustive checklist, or caller experiments were used.

**Bottom line:** The GAT consolidation itself is coherent, but it also removes the generic validity guarantees that made a `NonNullPtr` permission and borrowed reference usable through the trait. The concrete `Box` and `Arc` implementations partially recover those facts inside their predicates, while the `Frame` implementation makes validity conditional; generic RCU clients therefore no longer receive a contract establishing that the returned reference is valid. This should be repaired before merge at the trait boundary, rather than relying on implementation-specific predicates.

## High

None.

## Medium

### The consolidated trait no longer guarantees valid permissions or references

- **Guidelines:** `complete-external-contracts`, `api-postconditions`
- **Location:** `ostd/src/sync/rcu/non_null/mod.rs:43`
- **Quoted evidence:** The new trait declares `type Ref<'a>: 'a;`, `type Permission;`, and `type RefPermission<'a>;` (lines 43, 47, and 53), where the old declarations required `Permission: Inv`, `RefPermission: Inv`, and supplied validity obligations. The new `raw_as_ref` contract at lines 135-143 requires only `ptr_perm_match(...)` and ensures only `ref_rel_perm(ret, perm@)`; it no longer requires `perm@.inv()` or guarantees a valid returned reference. Likewise, `into_raw`, `from_raw`, `borrow_ref_perm`, `borrow_perm_as_ref_perm`, and `ref_as_raw` all lose their former `inv()` clauses.
- **Problem:** This is not merely moving validity into a common predicate. `Box` and `Arc` explicitly add `perm.inv()` to `ptr_perm_match`/`ref_rel_perm`, but `Frame::ptr_perm_match` at `ostd/src/mm/frame/frame_ref.rs:205-209` checks only the slot pointer, slot address, and initialization. `Frame::ref_rel_perm` at lines 222-227 is the implication `r.inv() ==> { perm.inv() && ... }`, so when `r.inv()` is unavailable it provides no validity fact. Consequently, generic RCU paths such as `RcuInner::read_with` (`ostd/src/sync/rcu/mod.rs:430-466`) can return `P::Ref<'a>` after proving `ptr_perm_match`, but their callable contracts no longer establish that the permission or returned reference satisfies its invariant. This weakens the abstraction precisely at the unsafe conversion boundary and prevents natural generic callers from recovering the reference's modeled contents and safety invariant.
- **Suggestion:** Restore a trait-level validity obligation. The direct repair is to retain `Permission: Inv`, `RefPermission<'a>: Inv`, and `Ref<'a>: Inv`, restore the removed `inv()` pre/postconditions (including the ref-permission-to-owned-permission lemma), and make `raw_as_ref` guarantee `ret.inv()`. If the GAT implementation cannot express those bounds, introduce one explicit trait predicate for owned-permission validity and one for reference validity, require/preserve them in every conversion and borrow method, and make `Frame::ptr_perm_match` or the conversion contracts include the full `FrameRawPerms::inv()` facts rather than a conditional implication.

## Low

None.

## Evidence check record

- Read all 913 lines of `diff.patch` and checked the affected trait and `Frame`/`Either` implementations against their `before/` and `after/` context.
- Refutation check: `Box<T>` and `Arc<T>` do place `perm.inv()` in their new `ptr_perm_match` and `ref_rel_perm` predicates, but that does not repair the generic contract, and the changed `Frame` predicates do not unconditionally imply either permission or reference validity.
- Invariant check: `FrameRawPerms::inv()` additionally requires a full fractional permission and `MetaSlot::perms_related`; those facts are absent from `Frame::ptr_perm_match`, which only carries address/initialization facts.
- Reuse/spec check: the patch introduces no competing standard-library external specification. The new `FrameRawPermsRef` reuses `FrameRawPerms` as its view and implements `Inv`; no separate evidence-backed specification-reuse finding was found.
- Workflow check: the patch contains no added or changed `#[verifier::rlimit(...)]`, so there is no `rlimit > 200` finding. It also contains no newly added or materially changed external specification for a `std`, `core`, or `alloc` API.
- Assumption/trust check: no newly added `assume`, `admit`, `external_body`, or axiom was found in the patch. The change does remove invariant obligations from a trusted unsafe trait boundary, as reported above.
- **No-verification disclosure:** This fast isolated pass did not run Verus, Rust tests, CI, or any synthetic client experiment. Conclusions are based only on static contract and source comparison; the supplied task treats verification as out of scope.
