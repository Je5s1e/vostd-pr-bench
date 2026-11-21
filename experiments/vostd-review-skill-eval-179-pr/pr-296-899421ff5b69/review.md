# Review: PR 296 isolated `diff.patch`

> Fast, non-exhaustive VOSTD review of the captured before/after files in `pr-296-899421ff5b69`.
> Scope: `diff.patch` (three changed paths: `vstd_extra/src/ghost_tree.rs`, `vstd_extra/src/lib.rs`, and `vstd_extra/src/undroppable.rs`).

**Bottom line:** The patch usefully removes several admits from `ghost_tree`, but it moves a fundamental default-node invariant into caller preconditions instead of stating it once on `TreeNodeValue`. This makes the public invariant-preservation API unnecessarily difficult to use, including for an empty-path insert that is definitionally a no-op. The invariant law should be established at the trait boundary before merge.

## High

No high-severity findings.

## Medium

### Default-node validity is imposed on every insert caller, even when insertion allocates no defaults

**Guideline:** `api-preconditions`  
**Location:** `vstd_extra/src/ghost_tree.rs:935`, `vstd_extra/src/ghost_tree.rs:1692`, `vstd_extra/src/ghost_tree.rs:1822`

**Evidence:** `Node::lemma_recursive_insert_preserves_inv` and `Tree::insert_preserves_inv` newly require:

```rust
forall|lv: nat| lv < L ==> #[trigger] T::default(lv).rel_children(None),
```

and `Tree::new_preserves_inv` separately requires:

```rust
#[trigger] T::default(0).rel_children(None),
```

Yet `TreeNodeValue` provides no law for that fundamental property. Its only related method is `default_preserves_rel_children(self, lv)`, which proves `self.rel_children(Some(Self::default(lv + 1)))` from properties of `self` (`ghost_tree.rs:353-359`). The excess is directly observable for `path.is_empty()`: `recursive_insert` returns `self` unchanged (`ghost_tree.rs:789-790`), and the preservation proof immediately uses the identity lemma (`ghost_tree.rs:953-954`), but the public lemma still demands both relationship implications and the universal default-node condition. Thus a legal no-op call must prove facts unrelated to its result.

**Problem:** The patch repairs an invariant proof by exporting an implementation-wide default-node obligation to every caller. This weakens the proof API and duplicates a type-level law across `new` and insert operations; for no-op and already-populated paths, the universal obligation is not needed at all.

**Suggestion:** Add a `TreeNodeValue` proof law that establishes `T::default(lv).rel_children(None)` for valid non-leaf levels (or otherwise make default-node validity part of the trait's canonical default contract), and consume it inside `Node::new_preserves_inv`. Then remove the universal caller requirement from the insert-preservation lemmas, or at minimum guard allocation-specific obligations by the path/seek case so the empty and non-allocating cases remain usable without them.

## Low

| Finding | Guideline | Detail |
|---|---|---|
| The public broadcast group silently stops exporting insert invariant preservation | `api-postconditions` | At `vstd_extra/src/ghost_tree.rs:1975`, `Tree::insert_preserves_inv` changes from an active `group_ghost_tree` member to `//Tree::insert_preserves_inv,`. The lemma remains public, but clients that rely on `broadcast use group_ghost_tree` no longer receive its invariant postcondition automatically. No replacement group or explanation is supplied. Restore the entry after fixing its contract, or provide and document a deliberate replacement group so the public proof bundle does not regress silently. |

## Evidence check record

- Read the complete captured `diff.patch` and checked the relevant before/after definitions of `TreeNodeValue`, `Node::inv_children`, `Node::new`, recursive insert/remove, the public `Tree` wrappers, and `group_ghost_tree`.
- Confirmed that `Node::inv_children` requires `value.rel_children(None)` for every absent child of a non-leaf node (`ghost_tree.rs:477-489`), while the trait has no default-to-`None` law (`ghost_tree.rs:336-359`).
- Confirmed from the definition that an empty-path recursive insert is exactly `self`, making the new universal default-node precondition unnecessary for that legal case (`ghost_tree.rs:780-801`).
- Searched the captured after-tree for `TreeNodeValue` implementations and uses of the changed preservation lemmas/group. The bundle contains one concrete implementation in `ostd/specs/mm/page_table/owners.rs`; no in-bundle `broadcast use group_ghost_tree` caller was found, so the group-removal item is rated low rather than medium.
- No changed `#[verifier::rlimit(...)]` and no new or materially changed `std`/`core`/`alloc` external specification appear in the diff.
- Trust check: the diff removes `admit()` uses from the changed `ghost_tree` proof bodies and introduces no new `admit`, `assume`, `external_body`, or axiom there. An unchanged concrete `TreeNodeValue` implementation elsewhere in the captured after-tree still contains an `admit`; it was treated as out of scope rather than reported as a new defect.
- Spec-reuse check: no evidence-backed duplicate of the newly added recursive preservation helpers or `remove_rel_children` predicate was found in the captured tree.

**No-verification disclosure:** This was the requested fast isolated static review. It did not run Verus, CI, standalone/client experiments, repository history, sub-agent persona passes, or an exhaustive guideline-rule audit. The repository-level coding-guideline pages were not present at the workspace root; findings are grounded in the checked-in VOSTD review skill's API criteria and the captured before/after source.
