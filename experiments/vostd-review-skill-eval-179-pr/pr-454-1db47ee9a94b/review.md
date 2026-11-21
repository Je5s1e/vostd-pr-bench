# Review: PR 454 snapshot `diff.patch`

> Produced from the VOSTD review skill's API-contract criteria, using the supplied before/after snapshot.
> Scope: `diff.patch`; changed files are `ostd/specs/mm/frame/linked_list/linked_list_owners.rs` and `ostd/src/mm/frame/linked_list.rs`.

**Bottom line:** The removal of `external_body` is valuable, and the successful result is now tied to a well-formed cursor. However, `cursor_mut_at` still does not specify its documented success condition and its failure paths discard the only tracked owner of the list. A verified caller therefore cannot establish that lookup succeeds for a member, or continue using the list after an ordinary `None` result. This should be fixed before merge.

## High

No high-severity findings.

## Medium

### A failed lookup loses the list owner and success is not specified

- **Guideline:** `api-postconditions`
- **Location:** `ostd/src/mm/frame/linked_list.rs:423`
- **Evidence:** The documentation says, “Gets a cursor at the specified frame if the frame is in the list” and “This method fails if the frame is not in the list” (lines 406–408). Yet the new contract only contains one-way implications from success: `r is Some ==> cursor_owner@ is Some` and the cursor-validity clauses (lines 445–448). It never guarantees `r is Some` when `owner.list` contains `frame`. Moreover, the input is an owned `Tracked<LinkedListOwner<M>>` (line 426), while both failure branches explicitly produce `Tracked(None)` (lines 502 and 507). `LinkedListOwner` contains the list's permission map (spec file lines 224–227), so no tracked owner remains available to a caller after a normal miss.
- **Problem:** The callable contract does not expose the method's documented membership test in either direction, and a fallible read-like operation consumes the proof resource needed for the next list operation on failure. The newly added invariant facts are sufficient to distinguish the cases—the member slot's permission value equals the nonzero `list_id` (spec file lines 232 and 261–262), whereas the nonmember precondition requires value zero—but the postcondition and ghost output do not return those facts/resources to callers.
- **Suggestion:** Specify the abstract result, for example `r is Some <==> exists|i: int| 0 <= i < owner.list.len() && owner.list[i].paddr == frame`, and make the ghost output preserve ownership on both branches. One concrete design is a tracked outcome enum carrying `CursorOwner<M>` on success and the (appropriately updated, if lazy ID allocation occurred) `LinkedListOwner<M>` on failure; then ensure the returned owner is invariant-preserving and well-formed for `final(self)`. Also relate `cursor_owner` to `r` in both directions rather than only under `r is Some`.

## Low

No low-severity findings.

## Evidence check record

- Read all 131 lines of `diff.patch` and compared both changed files against their before snapshots.
- Traced `LinkedListOwner::inv`, `inv_at`, `LinkedList::wf`, `CursorOwner::inv`, `CursorMut::wf`, `MetaRegionOwners::inv`, and the implementation's success and failure paths in the after snapshot.
- Checked repository callers: the only executable uses in this snapshot are unverified tests in `ostd/src/mm/frame/test.rs`; they do not repair the formal ownership gap.
- No `#[verifier::rlimit(...)]` change is present, and the patch adds no external specification for a `std`, `core`, or `alloc` API.
- No Verus run, history inspection, exhaustive guideline checklist, or isolated client experiment was performed, per the fast-review constraints. Findings are based on static source and contract evidence only.
