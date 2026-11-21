# Review: PR 534 snapshot (`diff.patch`)

> Produced from the authoritative `diff.patch` and the supplied before/after source snapshots.  
> Scope: eight changed OSTD memory-management files under `ostd/src/`; fast isolated review of maintainability, proof/trust assumptions, API contracts, invariants, rlimit use, and reusable specifications.

**Bottom line:** No high-severity issue was established by static inspection. One medium-severity proof-engineering issue remains: the patch relocates and retains an `rlimit(10000)` annotation, fifty times the VOSTD cap, without decomposing the proof obligation. The other contract and invariant changes reviewed have locally consistent caller-facing conditions in the available source.

## High

None.

## Medium

### Retained 10,000-unit solver limit masks an undecomposed proof obligation

- **Guideline:** `decompose-before-raising-rlimit`
- **Location:** `ostd/src/mm/page_table/cursor/mod.rs:3866`
- **Evidence:** The patch removes `#[verifier::rlimit(10000)]` from before the specification and adds the same annotation immediately after the specification; the resulting source contains `#[verifier::rlimit(10000)]` on `replace_cur_entry`.
- **Problem:** The changed annotation remains far above the workflow cap of 200. A 10,000-unit allowance makes verification performance and stability depend on one very large solver query and obscures which part of the extensive replacement contract is expensive.
- **Suggestion:** Split the proof into focused helper lemmas (in particular, separate mapping-update, returned-fragment, and per-slot preservation obligations), then reduce the function's rlimit to at most 200. If a temporary exception is unavoidable, document the measured bottleneck and a concrete removal plan rather than retaining 10,000 silently.

## Low

None.

## Evidence check record

- Read all 1,121 lines of `diff.patch`; treated it as the authoritative change set and used `before/` and `after/` only for surrounding context and stable line locations.
- Inspected the added `map_untracked_frames` metadata precondition and its use through `CursorMut::item_slot_in_regions`; the predicate quantifies every page-aligned address in the range, so it also supplies the sub-page slot-existence facts required for huge untracked mappings.
- Inspected the strengthened cursor-construction contracts and the newly verified `apply_sign_ext`, `is_valid_range`, `pte_index`, and `pte_index_bit_offset` bodies. Static source did not establish a missing precondition, weakened invariant, new trust escape, or caller-visible postcondition contradiction.
- No new or materially changed external specification for a `std`, `core`, or `alloc` API appears in the patch, so there is no upstream-reuse finding.
- The full repository coding-guideline pages were absent from this isolated snapshot; the rlimit finding uses the skill's explicit `decompose-before-raising-rlimit` cap of 200. No claim depending on an unavailable guideline page was reported.
- Per the fast-review instruction, no history inspection, Verus execution, build, CI run, exhaustive checklist, or isolated caller experiment was performed. Findings therefore reflect static evidence only; verification success was not independently confirmed.
