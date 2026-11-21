# Review: `diff.patch` (isolated PR snapshot)

> Produced from the VOSTD maintainability, proof-engineering, workflow, and API-contract review criteria in fast isolated mode.
> Scope: the four-file change recorded in `diff.patch`, using `before/` and `after/` only for surrounding context. `diff.patch` is authoritative.

**Bottom line:** I found no high- or medium-severity issue in the axiom-to-proof conversion, ghost-mode corrections, or removal of the unused spec argument. One low-severity documentation claim should be corrected because it describes proof state that the current model explicitly retired.

## High

None.

## Medium

None.

## Low

| Finding | Guideline | Detail |
|---|---|---|
| The revised proof description still claims a retired `raw_count` transition | `document-real-proof-debt` | At `ostd/specs/mm/embedding/segment.rs:148-153`, the changed prose says that after drop each slot's “`raw_count` is `pre_cover_count - 1`” and that the new proof “derives the range-wide transition” through `frame_drop_embedded`. However, `MetaSlotOwner` has no `raw_count` field, `lemma_segment_drop_embedded`'s contract at lines 182-221 constrains only the region/slot-owner state, and `frame_drop_embedded` likewise has no `raw_count` postcondition. The surrounding model explicitly says that “The per-slot `raw_count` cache that previously mirrored it has been retired” (`ostd/specs/mm/embedding/mod.rs:647-650`); cover-count change is instead derived from removing the `SegmentEntry` from the `segments` map. Reword this paragraph to say that the recursive proof derives the per-frame refcount transition, while segment removal separately derives the `segment_cover_count` decrement, and remove the claim that this lemma proves a `raw_count` update. |

## Evidence check record

- Read all 123 lines of the authoritative `diff.patch` and inspected the corresponding before/after context for all four changed files.
- Checked `lemma_segment_drop_embedded` against the exact `frame_drop_embedded` requires/ensures. The recursive step preserves the prior range-level contract; no concrete contract weakening was found.
- Checked `tracked_pop_level_owner` and its only caller. The returned guard is used only as a ghost value in proof calls, while the tracked continuation ownership is still removed, restored, and reinserted.
- Checked the removed `guard_ref` input to `dfs_acquire_lock`. It was not referenced by the contract; `entry_own.node().relate_guard(*cur_node)` remains the relationship tying the tracked owner to the mutable guard.
- No added or changed `#[verifier::rlimit(...)]` was present, and the patch adds no material external specification for a `std`, `core`, or `alloc` API.
- Per the requested fast-review override, I did not inspect Git history, run Verus or other verification, perform caller experiments, or apply an exhaustive rule-by-rule pass. Findings are based on static evidence in `diff.patch` and the supplied before/after snapshots only.
