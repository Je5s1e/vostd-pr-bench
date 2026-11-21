# Review: PR 628 snapshot 096c166e5ce6

> Scope: authoritative `diff.patch`, checked against the captured `before/` and `after/` trees. The patch changes only `ostd/specs/mm/embedding/list_store.rs`.

**Bottom line:** The patch removes three trusted axioms, but the new checked `push_back_embedded` proof preserves a contract that inserts before the existing last element rather than at the tail. That contradicts the documented `push_back` behavior and makes the abstract sequence order wrong for every nonempty list. This should be corrected before merge; the two pop specializations match their generic helper contracts.

## High

### `push_back_embedded` proves insertion at the wrong position

- **Guideline:** `api-postconditions`
- **Location:** `ostd/specs/mm/embedding/list_store.rs:471` and `ostd/specs/mm/embedding/list_store.rs:522`
- **Evidence:** The new rustdoc says the frame is “spliced in at the *tail*” (lines 449–452), but the postcondition is `old(owner).list.insert(old(owner).list.len() - 1, ...)` for a nonempty list (lines 471–474), and the proof calls `insert_before_at_embedded` with `n = owner.list.len() - 1` (lines 522–527). The reused helper explicitly inserts at position `n` and accepts the actual tail position `n == len` (lines 595–600 and 607 onward). The underlying executable API also documents “inserted at the back” while constructing a back cursor whose model index is `len - 1`; `CursorMut::insert_before` inserts at precisely that index (`ostd/src/mm/frame/linked_list.rs:282-320`, `ostd/specs/mm/frame/linked_list/linked_list_owners.rs:1178-1201`, and `ostd/src/mm/frame/linked_list.rs:1136-1143`). For a model `[a, b]`, the stated operation therefore produces `[a, new, b]`, not `[a, b, new]`.
- **Problem:** The formal postcondition does not expose the documented abstract result, and the newly checked specialization confirms the same off-by-one behavior instead of a true back insertion. Any proof that depends on list order after `push_back` receives the wrong sequence model; the static evidence also shows that this mismatch originates in the executable API's back-cursor construction/specification rather than in the generic insertion helper.
- **Suggestion:** Repair `LinkedList::push_back` to insert at the ghost/non-element cursor at index `len` (using the existing ghost-owner abstraction as appropriate), specify its result as `old(owner).list.insert(old(owner).list.len(), ...)`, and make `push_back_embedded` call `insert_before_at_embedded` with `n = owner.list.len()`. Update the affected frame-condition indices to describe the real tail neighbor, then re-run verification.

## Medium

None.

## Low

None.

## Evidence check record

- Read the complete authoritative 86-line patch and compared every changed hunk with the captured before/after source.
- Checked the exact contracts of `insert_before_at_embedded` and `take_at_embedded`. The front and back removal bodies use indices `0` and `len - 1`, respectively, which match their promised removals. The back insertion body uses `len - 1`, while its generic helper permits and defines insertion at `len`.
- Traced the discrepancy through `LinkedList::push_back`, `CursorOwner::back_owner`, `CursorOwner::ghost_owner`, and `CursorMut::insert_before`; these definitions rule out a sentinel or alternate-index interpretation that would make `len - 1` a tail insertion.
- Searched the patch for verifier resource-limit changes and new or materially changed `std`/`core`/`alloc` external specifications. None are present, so the `rlimit > 200` and upstream-spec workflow checks are not triggered.
- The patch reuses the existing generic embedded insertion/removal specifications; no duplicate specification was introduced. The remaining issue is selection of the wrong valid index and the corresponding API contract.
- Per the requested fast-review override, no Verus run, caller experiment, repository history analysis, or exhaustive guideline checklist was performed. The finding is based on direct static contract and implementation evidence only.
