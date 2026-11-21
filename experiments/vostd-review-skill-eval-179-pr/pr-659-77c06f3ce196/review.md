# Review: PR #659 snapshot (`diff.patch`)

> Fast, non-exhaustive review of the supplied patch and its `before/` / `after/` context against the VOSTD maintainability, proof-engineering, and API-contract criteria. Scope: `diff.patch`, affecting `ostd/specs/mm/embedding/io.rs` and `ostd/specs/mm/embedding/mod.rs`.

**Bottom line:** The patch removes several local axioms, but the kernel-owner constructors still derive unconditional validity from a broader axiom whose formal contract does not contain the kernel-range restriction stated in its documentation. It also turns the modeled read/write transfers into concrete no-ops, so the embedding cannot expose the range effects promised by the executable APIs. Both should be addressed before merge; no high-severity issue was found in this fast pass.

## High

None.

## Medium

### The new constructors use the kernel-memory axiom without its documented domain restriction

- **Guidelines:** `complete-external-contracts`, `centralize-trusted-boundaries`
- **Location:** `ostd/specs/mm/embedding/io.rs:137` and `ostd/specs/mm/embedding/io.rs:163`
- **Evidence:** Both new proof bodies call `let tracked mem_view = axiom_kernel_mem_view(range);` for a range derived only from an overflow check. The axiom at `ostd/specs/mm/io.rs:52-64` has no `requires` clause and therefore formally returns a mapped, initialized `MemView` for every `Range<usize>`, while its own documentation limits the justification to bytes in `[KERNEL_BASE_VADDR, KERNEL_END_VADDR)`. The embedding compounds this at `ostd/specs/mm/embedding/mod.rs:1041-1042`, where both kernel-construction operations have `op_pre == true`.
- **Problem:** Replacing the specialized axioms with proof functions does not actually discharge the trust assumption; it routes arbitrary addresses through an axiom whose contract is stronger than its stated kernel-memory justification. The resulting `VmIoOwner::inv()` and read/write-view facts are therefore available even for ranges for which the executable `from_kernel_space` contract only promises them conditionally.
- **Suggestion:** Put the ordered, non-overflowing kernel-range condition on `axiom_kernel_mem_view`, then thread that condition through `tracked_vm_{reader,writer}_from_kernel_space_embedded`, `new_kernel_vm_io_step`, and `op_pre`. If the intended trust assumption truly is that every address range is mapped and initialized, state and justify that stronger boundary explicitly instead of describing it as a kernel-range fact.

### The constructive transfer model hard-codes zero-byte reads and makes writes no-ops

- **Guideline:** `api-postconditions`
- **Location:** `ostd/specs/mm/embedding/io.rs:205` and `ostd/specs/mm/embedding/mod.rs:2522`
- **Evidence:** `tracked_vm_reader_read_embedded` now consists of `dest_owner.split(0)`. By the checked `VmIoOwner::split` contract (`ostd/specs/mm/io.rs:381-389`), this forces the returned owner's range to `[old.start, old.start)` and leaves the destination range start unchanged. In the same patch, `step_write` deletes `io::write_step(&mut src, &mut dst);`, leaving only extract/reinsert. In contrast, the executable `VmReader::read` contract at `ostd/src/mm/io.rs:803-810` states that both cursors advance by `r` and that `consumed_w.range.end == old(owner_w).range.start + r`; the executable writer contract likewise states exact cursor advancement (`ostd/src/mm/io.rs:560-564`).
- **Problem:** These functions are documented as mirrors of the executable transfers, but the new implementations model every read as transferring zero bytes and every write as changing no owner state. Their weak postconditions allow this, so natural embedding clients cannot recover even an abstract transfer length or the corresponding range effects; successful verification of store invariants would not check the documented transfer behavior.
- **Suggestion:** Represent the transferred byte count in the operation/step interface and split/advance the owners by that amount, with postconditions tying both final ranges and `consumed_w` to it. If the embedding intentionally abstracts all data-transfer effects away, rename and document these transitions as explicit no-op abstractions and remove claims that `consumed_w` covers the “just-written portion”; do not present the current zero-length construction as the executable operation's effect.

## Low

| Finding | Guideline | Detail |
|---|---|---|
| Ownership-proof helper uses a generic lemma prefix | `name-proof-roles` | `ostd/specs/mm/embedding/io.rs:213` renames the unit-returning helper to `lemma_vm_writer_fill_zeros_embedded`, although it mutates a tracked `VmIoOwner`. Use the `tracked_` role prefix consistently (for example, `tracked_vm_writer_fill_zeros_embedded`). |

## Evidence check record

- Read all 285 lines of `diff.patch` and inspected the corresponding `before/` and `after/` source around every changed hunk.
- Checked the exact contracts of `VmIoOwner::inv`, `VmIoOwner::split`, `axiom_kernel_mem_view`, executable `VmReader::read` / `VmWriter::write`, the embedding `op_pre`, and the store transition callers.
- Searched the scoped patch for `#[verifier::rlimit(...)]`; none was added or changed, so the `> 200` workflow check was not triggered.
- Searched the available `after/` tree for relevant owner constructors, split operations, and uses of `axiom_kernel_mem_view`. The patch reuses the existing `VmIoOwner::split`; no separate duplicate specification was established in this fast pass.
- The snapshot does not include the repository's full coding-guideline pages, so guideline names and criteria were taken from the supplied VOSTD review skill and checked against the available source context.
- Per the requested fast-review constraints, no Verus run, caller experiment, CI verification, repository history analysis, sub-agent pass, or exhaustive checklist was performed. Findings are based on static contract and source evidence only.
