# Review: PR 617 supplied snapshot

> Produced from the supplied `diff.patch` and its `before/` and `after/` source snapshots, using the VOSTD maintainability, proof-engineering, and API-contract criteria.
> Scope: the authoritative 782-line patch changing `ostd/src/mm/dma/dma_stream.rs`; no repository history, Verus run, exhaustive checklist, or caller experiment was performed under the fast-review override.

**Bottom line:** The proof cleanup is generally focused, but the new public getter contracts do not actually relate their ghost snapshots to the `DmaStream` being queried. Consequently, callers cannot use these contracts to establish that the returned address, direction, or size belongs to this stream, and the same gap prevents useful correlation across getter calls.

## High

None.

## Medium

### The getter snapshots are not tied to the receiver

- **Guideline:** `api-postconditions`
- **Location:** `ostd/src/mm/dma/dma_stream.rs:464` (same pattern at lines 490, 551, 580, and 600)
- **Evidence:** Each changed getter introduces an output such as `-> inner_snapshot: Ghost<DmaStreamInner<M>>` and ensures only `inner_snapshot@.inv()` plus `r == inner_snapshot@.start_daddr` (or the corresponding `direction`/`segment` projection). The implementation assigns `inner@.data` to the output, but the callable postcondition contains no relation between `inner_snapshot` and `self`, `self.inner`, or a receiver-specific identity. `read_inner` likewise promises only `self.inner.wf()` and `r@.inv()` at lines 444–448.
- **Problem:** The contract permits the output witness to be any invariant-satisfying `DmaStreamInner<M>`, including one unrelated to this receiver. Thus `daddr`, `direction`, `paddr`, `nframes`, and `nbytes` do not formally expose the documented value of this stream; separate calls also yield unrelated witnesses, so a caller cannot correlate the address and size as fields of the same protected state.
- **Suggestion:** Introduce a receiver-specific abstract state/snapshot relation (for example, a predicate connecting `self.inner` or its stable owner identity to `DmaStreamInner<M>`), have `read_inner` expose that relation for the acquired guard, and preserve it in each getter's output contract. If concurrent mutation intentionally permits different linearization snapshots, specify that explicitly while still proving that each snapshot is a state of this receiver rather than merely an arbitrary invariant value.

## Low

None.

## Evidence check record

- Treated `diff.patch` as authoritative and read all 782 lines.
- Compared the changed regions against the complete `before/ostd/src/mm/dma/dma_stream.rs` and `after/ostd/src/mm/dma/dma_stream.rs` snapshots, including the getter implementations, `read_inner`, reader/writer contracts, and affected `VmIo` callers.
- Searched the patch for `#[verifier::rlimit(...)]`; none was added or changed, so the numeric rlimit check was not triggered.
- The patch adds no external specification for a `std`, `core`, or `alloc` API, so the reusable-external-spec workflow check was not triggered.
- The getter finding was checked against the callable postconditions rather than inferred from implementation intent: no clause connects `inner_snapshot` to the receiver.
- **No-verification disclosure:** Per the fast-review override, no Verus execution, isolated client experiment, repository-history inspection, or exhaustive rule-by-rule verification was performed. Conclusions are static and limited to the supplied patch and snapshots.
