# Review: PR #382 snapshot `045fa97a6577`

> Fast, non-exhaustive review of `diff.patch` with the corresponding `before/` and `after/` source snapshots.
> Scope: the changes captured in `pr-382-045fa97a6577/diff.patch`; no repository history or live PR metadata was consulted.

**Bottom line:** The patch removes several admits, but two of the replacements move the missing proof into trusted declarations whose contracts are not justified by their inputs or executable behavior. Most seriously, the traversal helper is now assumed never to return `None` even though its implementation and documentation explicitly retain that outcome. The huge-page split also obtains linear slot ownership and slot-state facts from a strengthened placeholder axiom rather than threading the real permission.

## High

### The trusted traversal contract excludes an executable `None` result

- **Guidelines:** `complete-external-contracts`, `api-postconditions`
- **Location:** `ostd/src/mm/page_table/cursor/locking.rs:166`
- **Evidence:** The changed `#[verifier::external_body]` contract unconditionally adds `r is Some` (`locking.rs:166`). The same function's rustdoc says that on a stray locked node "it will return `None`. The caller should retry" (`locking.rs:155-157`), and its executable body still contains `if is_stray { return None; }` (`locking.rs:327-329`). `lock_range` then replaces `assert(subtree_root is Some) by { admit() }` with a bare assertion (`locking.rs:83`), so the new trusted postcondition is exactly what discharges the former admit.
- **Problem:** The external-body contract contradicts a reachable result that the function explicitly implements. Verification can therefore reason past the retry case and unwrap the result using a false trusted fact; this is not a proof of the old obligation.
- **Suggestion:** Do not promise `r is Some`. Preserve the documented `Option` behavior, restore the retry loop in `lock_range` (or prove from explicit, truthful preconditions that the stray case is impossible), and give the helper conditional postconditions for both `Some` and `None` outcomes.

### The split proof fabricates a slot permission and unrelated region facts

- **Guidelines:** `centralize-trusted-boundaries`, `complete-external-contracts`
- **Location:** `ostd/specs/mm/page_table/node/entry_owners.rs:104`
- **Evidence:** `placeholder_slot_perm` remains a public axiom that returns a tracked `PointsTo<MetaSlot>` without consuming it from `regions.slots`; the patch strengthens it to guarantee initialization, `wf`, non-`UNUSED` refcount, and `path_if_in_pt is None` (`entry_owners.rs:104-114`). Its only new semantic precondition is `regions.inv()` plus address bounds/alignment. But `MetaRegionOwners::inv` guarantees only `MetaSlotOwner::inv()` for every `slot_owners` entry and relates a `PointsTo` value to the owner only when the index is present in `regions.slots` (`ostd/specs/mm/frame/meta_region_owners.rs:57-83`); it does not imply non-`UNUSED` or `path_if_in_pt is None`. The split calls the axiom at `ostd/src/mm/page_table/node/entry.rs:780` and immediately uses the newly asserted region facts at lines 805-821 to replace prior admits.
- **Problem:** The axiom can be called for any aligned in-range address, including a slot whose real permission remains in `regions.slots` or whose owner has a different path/refcount state. It both duplicates a linear ownership capability and asserts state facts not entailed by its preconditions, making the resulting `Child::Frame` invariant trusted rather than verified.
- **Suggestion:** Remove `placeholder_slot_perm` from this path. Split the huge-frame ownership representation so the real child `PointsTo<MetaSlot>` permissions are derived/partitioned and threaded into each child, with the required refcount/path facts proved from that operation. If a temporary trust boundary is unavoidable, place a narrowly scoped boundary in the ownership module and require the exact permission/state facts as inputs instead of asserting them as outputs.

## Medium

### `lock_range` no longer exposes the invariant its sole wrapper promises

- **Guideline:** `api-postconditions`
- **Location:** `ostd/src/mm/page_table/cursor/locking.rs:43`
- **Evidence:** The old contract guaranteed `ret.0.invariants(*ret.1, *regions, *guards)`, `ret.1.in_locked_range()`, and `ret.0.level < ret.0.guard_level`; the patch deletes all three and retains only `ret.0.level <= ret.0.guard_level` plus address/frame properties (`locking.rs:43-55`). The sole call at `ostd/src/mm/page_table/cursor/mod.rs:264-266` is the success result of public `Cursor::new`, whose contract still promises those deleted invariant, locked-range, and strict-level facts (`cursor/mod.rs:226-234`).
- **Problem:** The callee's callable contract no longer connects its returned `CursorOwner` to `regions` or `guards`, so a caller cannot establish the natural cursor invariant or the wrapper's still-advertised success contract from `lock_range`'s postconditions. Weakening the internal API contract also hides the central result of acquiring the range lock.
- **Suggestion:** Restore the relational invariant, `in_locked_range`, and strict-level postconditions on `lock_range`, and prove them using truthful contracts for the traversal/DFS helpers. If the algorithm can legitimately return at the guard level, change the outer API and its documented semantics consistently rather than weakening only the helper.

## Low

No evidence-backed low-severity findings in this fast pass.

## Evidence check record

- Read all 472 lines of `diff.patch` and inspected the relevant `before/` and `after/` context for `entry_owners.rs`, `entry.rs`, `locking.rs`, `cursor/mod.rs`, and `meta_region_owners.rs`.
- Checked every changed trusted construct shown by the patch (`axiom`, `external_body`, `assume_specification`, and removed `admit` sites) for the findings above.
- No changed `#[verifier::rlimit(...)]` was present, so the `rlimit > 200` check was not triggered. No newly added or materially changed external specification for a `std`, `core`, or `alloc` API was present, so the upstream-spec check was not triggered.
- Searched the snapshot for callers of `lock_range` and `placeholder_slot_perm`; the cited call sites are the only matches.
- The standalone guideline pages under `docs/coding-guidelines/` are not included in this workspace snapshot. Rule identifiers and review criteria therefore come from the checked-in `vostd-code-review` skill/persona instructions; this fast pass did not attempt an exhaustive rule-by-rule audit.
- **No-verification disclosure:** Per the requested fast-review mode, no Verus build, proof experiment, CI run, history inspection, or isolated caller experiment was performed. Findings are based on static contract/body and before/after evidence only.
