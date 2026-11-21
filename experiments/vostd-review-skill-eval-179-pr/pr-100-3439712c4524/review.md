# Review: `diff.patch` (fast static snapshot review)

> Produced from the VOSTD review criteria in a deliberately fast, non-exhaustive mode.
> Scope: `pr-100-3439712c4524/diff.patch`; `after/` and `before/` were used only for nearby context and source line numbers. No Verus, build, tests, history lookup, caller experiment, or other verification was run.

**Bottom line:** The revised cursor invariant is inconsistent with the cursor constructed by the changed test, so the new `map` precondition cannot be established there. In addition, `move_forward` promises an address update that its implementation does not perform for an unaligned current address, while two changed public contracts omit the key semantic relationship/effect callers need. These contract issues should be corrected before relying on the new verification surface.

## High

### The new cursor invariant contradicts the changed test cursor

- **Check:** `api-preconditions`
- **Location:** `lock-protocol/src/mm/page_table/cursor/mod.rs:128` (with the changed construction at `lock-protocol/src/exec/test_map.rs:133`)
- **Evidence:** `va_wf` requires `self.barrier_va.start < self.barrier_va.end < MAX_USERSPACE_VADDR`, and `map` now requires `old(self).0.wf(old(spt))`. The changed test constructs `barrier_va: 0..MAX_USERSPACE_VADDR + PAGE_SIZE()` and then calls `cursor.map(...)`.
- **Problem:** That cursor cannot satisfy the newly required `va_wf`, because its range end is explicitly greater than `MAX_USERSPACE_VADDR`. This makes the changed call site's new `map` precondition contradictory on static inspection.
- **Suggestion:** Decide and document the intended half-open range boundary, then make `va_wf` and cursor construction agree (for example, permit the intended exclusive endpoint if `MAX_USERSPACE_VADDR + PAGE_SIZE()` is valid, or construct the test with an endpoint accepted by the invariant). Add an assertion of the complete `cursor.0.wf(&sub_page_table)` before the call.

### `move_forward` promises the wrong next address

- **Check:** `api-postconditions`
- **Location:** `lock-protocol/src/mm/page_table/cursor/mod.rs:229`
- **Evidence:** The new postcondition is `self.va == old(self).va + page_size::<C>(self.level)`, but the body computes `let next_va = align_down(self.va, page_size) + page_size; self.va = next_va;`. The new `wf` precondition only bounds `va`; it does not require alignment at `self.level`.
- **Problem:** For an unaligned old address, `align_down(old_va, page_size) + page_size` is not `old_va + page_size`. Thus the strengthened postcondition does not follow from the implementation and stated preconditions.
- **Suggestion:** Either require `old(self).va % page_size::<C>(old(self).level) == 0` (and preserve the relevant level equality), or specify the result as `align_down(old(self).va, page_size::<C>(old(self).level)) + page_size::<C>(old(self).level)`.

## Medium

### `map` no longer specifies that it creates the requested mapping

- **Check:** `api-postconditions`
- **Location:** `lock-protocol/src/mm/page_table/cursor/mod.rs:386`
- **Evidence:** The changed ensures list contains only well-formedness, allocator invariants, constant cursor fields, and unchanged `va`/`level`; it is immediately followed by `// TODO: Add the mapping model and ensure the mapping is built.` The prior mapping-oriented `sub_page_table_valid_after_map(...)` postcondition was removed.
- **Problem:** A caller cannot derive that the supplied `frame` was mapped at the cursor address, nor what `res` means. The central functional effect of this public mutating API is therefore absent from its contract.
- **Suggestion:** Add a mapping-model postcondition connecting the old cursor address, `frame`, `prop`, the resulting page-table state, and `res` (including the prior mapping when one existed) before treating this API as verified.

### `Entry::new_at` no longer connects the returned entry to `node` and `idx`

- **Check:** `api-postconditions`
- **Location:** `lock-protocol/src/mm/page_table/node/entry.rs:206`
- **Evidence:** The patch removes `res.pte.pte_paddr() == index_to_paddr(node.paddr() as int, idx as int)`. The replacement postconditions state `res.node == node` and `res.idx == idx`, but the only PTE-address clause is self-referential: `res.pte.pte_paddr() == exec::get_pte_from_addr(res.pte.pte_paddr(), spt).pte_addr`.
- **Problem:** The contract no longer states that the returned PTE is the entry at `idx` in `node`. Consequently, callers cannot use this API contract to associate the returned PTE with its input location; `Cursor::cur_entry` nevertheless attempts to promise exactly that association.
- **Suggestion:** Restore the direct address relation using the renamed helper: `res.pte.pte_paddr() == index_pte_paddr(node.paddr() as int, idx as int)`, then derive the model lookup facts from that address.

## Low

No low-severity findings were recorded in this fast review.

## Evidence check record

- Reviewed `diff.patch` as the authoritative scope and inspected only nearby `before/`/`after/` source for line numbers and direct context.
- Searched the scoped snapshots for `assume`, `admit`, `external_body`, `rlimit`, and preserve-exec-code markers. The patch does not add a new `admit`, `external_body`, rlimit over 200, or preserve-exec-code change. Existing assumptions remain in the surrounding implementation; this fast review did not re-audit unchanged trust debt.
- Confirmed the cited clauses and constructions directly in the `after/` snapshot.
- No verification command, compilation, test, history lookup, or isolated caller experiment was run; conclusions are static and evidence-bounded.
