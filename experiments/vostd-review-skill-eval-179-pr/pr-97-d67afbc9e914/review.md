# Review: `diff.patch` (PR 97 fixture `d67afbc9e914`)

> Produced from the supplied before/after snapshots and `diff.patch`, using the VOSTD maintainability, proof-engineering, and API-contract criteria.  
> Scope: fast, non-exhaustive review of `pr-97-d67afbc9e914/diff.patch`; surrounding context was read from the matching `before/` and `after/` files.

**Bottom line:** The new level check changes executable traversal behavior: after descending to a level-1 page table, `take_next` now exits without examining or unmapping the base-page entry and reports the whole requested range as not mapped. This conflicts directly with the function's documented behavior and should block the change. The widened `Entry::replace` contract also still does not expose the documented returned old child, so verified callers cannot reason about the result.

## High

### `take_next` stops before examining level-1 entries

- **Guideline:** `preserve-exec-code`
- **Location:** `lock-protocol/src/mm/page_table/cursor/mod.rs:718`
- **Quoted evidence:** The loop changed from `while self.0.va < end` to `while self.0.va < end && self.0.level > 1`. `push_level` establishes `self.level == old(self).level - 1` (`cursor/mod.rs:327`) and the `PageTableRef` arm calls it (`cursor/mod.rs:755-768`). The loop's fall-through result is `PageTableItem::NotMapped { va: start, len }` (`cursor/mod.rs:864-865`), while the rustdoc promises that the function finds and removes the first mapped page in the following range (`cursor/mod.rs:673-686`).
- **Problem:** When traversal descends from level 2 to level 1, the added guard makes the next loop test fail even though `self.0.va < end`. The level-1 entry is therefore never inspected or replaced, and the function returns `NotMapped` for a range that may contain a mapped base page. This is not a behavior-preserving proof-only edit, and no `Origin Rust:` record or unchanged-behavior demonstration accompanies it.
- **Suggestion:** Restore the executable loop condition `while self.0.va < end`. Carry the fact needed by the body through a suitable invariant or restructure the proof around the level-1 case without excluding that case from runtime traversal; retain an adjacent `Origin Rust:` block only if an executable rewrite is genuinely unavoidable and demonstrate semantic equivalence.

## Medium

### The widened `replace` API does not specify its returned old child

- **Guideline:** `api-postconditions`
- **Location:** `lock-protocol/src/mm/page_table/node/entry.rs:108`
- **Quoted evidence:** The patch removes `!old(spt).ptes@.value().contains_key(self.pte.pte_paddr() as int)` from `replace`'s `requires`, so replacement of a present entry is now admitted. Its documentation says, `The old child is returned.` (`entry.rs:93-95`), but the `ensures` block at lines 113-123 never mentions the named return value `res`; `match new_child { _ => true }` is also tautological.
- **Problem:** The contract change makes the old, present mapping a meaningful caller-visible result, yet no postcondition relates `res` to the pre-state PTE or `old(spt)`. A verified caller can receive the value but cannot establish that it is the child that was replaced, which is the API's stated purpose.
- **Suggestion:** Add a postcondition that characterizes `res` from the pre-state entry/PTE model (and, where useful, characterizes the installed `new_child` in the final state). Express the exact result with `returns` if the existing model provides a type-correct expression; otherwise use a non-tautological `ensures` relation over `res` and `old(spt)`.

## Low

No evidence-backed low-severity findings.

## Evidence check record

- Read the complete supplied `diff.patch` and compared both changed files against their matching `before/` and `after/` snapshots.
- Checked the traversal premise statically: the `PageTableRef` branch calls `push_level`, whose postcondition reduces `level` by one; the added loop guard excludes the resulting level-1 state before `cur_entry` and `replace` execute.
- Checked the `replace` signature and postconditions statically: the removed precondition widens accepted pre-states, while no remaining postcondition references `res` or relates it to the old entry.
- No `#[verifier::rlimit(...)]` change appears in the patch, so the `rlimit > 200` check was not triggered. No new or materially changed `std`/`core`/`alloc` external specification appears, so the upstream-spec-reuse workflow check was not triggered. No new spec/model/lemma was introduced for which a concrete reuse candidate could be established from the supplied scope.
- **No-verification disclosure:** Per the requested fast mode, no Verus run, isolated caller experiment, history inspection, or exhaustive guideline checklist was performed. The findings are based on source-level before/after evidence only.
