# Review: PR 547 snapshot

> Scope: `diff.patch` was treated as authoritative and reviewed against the corresponding `before/` and `after/` trees. The patch changes only `ostd/src/mm/page_table/cursor/mod.rs`, at `path_slot_as_mut` and `Cursor::cur_entry`.

**Bottom line:** No high- or medium-severity issue is supported by the static evidence. The new `path_slot_as_mut` contract accurately frames the selected slot and preserves every other array slot, while `cur_entry` retains the cursor invariants and all stable scalar fields without incorrectly promising that the mutably borrowed guard is unchanged. One nearby comment still describes the helper as an `external_body` trust boundary even though this patch removes that attribute.

## High

None.

## Medium

None.

## Low

| Finding | Guideline | Detail |
|---|---|---|
| Stale trust-boundary explanation at `ostd/src/mm/page_table/cursor/mod.rs:126` | `document-real-proof-debt` | The comment says, “`external_body` because Verus's mut-ref model can't see through the `array[idx].as_mut()` reborrow chain” and later calls the contract a “trust boundary,” but the patch removes `#[verifier::external_body]` and verifies the ordinary Rust body at lines 144–148. This now misstates both the current constraint and the trusted-code surface. Remove the obsolete explanation or replace it with a brief description of why the explicit frame postconditions are useful to callers. |

## Evidence check record

- Read the complete authoritative `diff.patch` and inspected both snapshots around the two changed hunks.
- At `ostd/src/mm/page_table/cursor/mod.rs:133-148`, checked that the helper requires a valid occupied slot, returns its old guard value, keeps the selected slot occupied and tied to the final returned borrow, and preserves every non-selected slot.
- At `ostd/src/mm/page_table/cursor/mod.rs:1919-1985`, checked the weakened `cur_entry` frame condition against `Cursor::inv`, `Cursor::wf`, the unchanged `CursorOwner`, and the returned `Entry` relationship. The contract preserves `level`, `guard_level`, `va`, and `barrier_va`; `final(self).wf(*final(owner))` continues to connect live path slots to the unchanged continuation guards. The removed whole-value equality would be unnecessarily strong for a function returning a mutable entry handle into `self.path`.
- The diff adds no `#[verifier::rlimit(...)]`, so the `> 200` workflow check is not triggered. It adds or changes no external specification for a `std`, `core`, or `alloc` API, so the spec-reuse workflow check is not triggered.
- No assumptions, admits, or new trusted bodies are introduced; instead, one `external_body` is removed.
- Per the fast-review override, no Verus run, history analysis, caller experiment, or other dynamic verification was performed. Conclusions are based on static source and contract inspection only.
