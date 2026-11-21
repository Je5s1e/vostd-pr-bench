# Review: supplied `diff.patch` snapshot

> Produced by a fast, non-exhaustive static VOSTD review of the supplied patch.
> Scope: `diff.patch` is authoritative; `before/` and `after/` were used only for nearby context and after-change line numbers. No Verus, CI, history lookup, or isolated caller experiment was run.

**Bottom line:** The refactoring weakens the cursor's central path invariant: a populated slot is no longer required to contain a guard whose level equals that slot's level. That is a merge-blocking contract regression because `Cursor::wf` delegates to this predicate and later code indexes `path` by `self.level`. The patch also duplicates a fact already contained in `ancestors_match_path` as an independent caller precondition.

## High

### `path_wf` no longer ties each guard's level to its path slot

- **Guideline:** `api-postconditions`
- **Location:** `lock-protocol/src/mm/page_table/cursor/mod.rs:189`
- **Quoted evidence:** The new outer predicate says only `self.level <= i <= self.guard_level ==> { guard_option.is_some(); self.path_item_wf(guard_option.unwrap(), spt) }`. Inside `path_item_wf`, line 158 checks `cur_frame == self.path[path_index_at_level(cur_frame.level_spec())].unwrap()`, while lines 172–176 check the entry indexed by `cur_frame.level_spec()`; neither clause states that the outer slot level `i` equals `cur_frame.level_spec()`. By contrast, the removed predicate explicitly required `guard_option.unwrap().level_spec() == i as int` for every `self.level < i <= self.guard_level`.
- **Problem:** A path can satisfy the new formula with the same guard duplicated in slot `i` and in the slot named by that guard's own level, even when the guard stored at slot `i` has a different level. Thus `Cursor::wf` no longer establishes the documented representation invariant that “the level N page table lock guard is at index N - 1,” and consumers that select the current node by `self.path[self.level - 1]` can receive a guard for another level.
- **Suggestion:** Pass the expected level into `path_item_wf` (or retain the check in `path_wf`) and require `cur_frame.level_spec() == i as int`. Keep the helper's ancestor-chain facts, but do not derive the expected slot from `cur_frame.level_spec()` itself.

## Medium

### `push_level` repeats a fact already required by `ancestors_match_path`

- **Guideline:** `reuse-existing-specifications`
- **Location:** `lock-protocol/src/mm/page_table/cursor/mod.rs:333`
- **Quoted evidence:** `push_level` newly requires both `child_pt.level_spec() == old(self).level - 1` (line 333) and `old(self).ancestors_match_path(spt, child_pt)` (line 335), while the definition of `ancestors_match_path` already contains `guard.level_spec() == self.level - 1` at line 221.
- **Problem:** The added clause makes every caller prove the same property twice and lets the two contract statements drift. The fact being hidden by a closed predicate is a proof-access issue, not a reason to duplicate its semantics in the API contract.
- **Suggestion:** Remove the standalone level precondition and reveal `ancestors_match_path` in the proof where the contained fact is needed, or add a small checked lemma that projects the level fact from the predicate.

## Low

No low-severity findings.

## Evidence check record

- **Review mode:** Fast static review only; no verification was run.
- **Authoritative evidence:** `diff.patch`, checked in full.
- **Context checked:** `after/lock-protocol/src/mm/page_table/cursor/mod.rs:122-353` and the corresponding `before/` region.
- **Trust-boundary scan:** The patch removes one local `assume` from `push_level` and adds no `assume`, `admit`, `external_body`, or axiom. Existing assumptions outside the changed hunks were not treated as patch findings.
- **Executable-code preservation:** The changed executable statements are limited to a proof-only assertion in `pop_level`, a strengthened `push_level` contract, and removal of proof/assumption blocks; no runtime expression rewrite was identified in the supplied diff.
- **Workflow checks:** No changed `#[verifier::rlimit(...)]` and no new or materially changed `std`/`core`/`alloc` external specification appear in the patch.
- **Experiments and verification:** None, per the requested fast-review constraints. The high-severity counterexample is a direct logical reading of the new predicates; it was not compiled or checked with Verus.

