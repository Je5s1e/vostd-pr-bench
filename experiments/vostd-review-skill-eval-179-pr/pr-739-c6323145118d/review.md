# Review: PR 739 snapshot c6323145118d

> Fast isolated VOSTD review using `diff.patch` as the authoritative change set and the `before/` and `after/` trees for context.
> Scope: `ostd/src/mm/kspace/kvirt_area.rs` at the five hunks recorded in `diff.patch`.

**Bottom line:** No actionable findings were identified. The change strengthens observable contracts (`range` now exposes its exact result, while `map_frames` now guarantees both the returned area's invariant and preservation of the metadata-region invariant), removes an unjustified local `assume`, and trims proof blocks whose facts are already supplied by the function precondition and `cursor.map`'s strengthened contract. No executable behavior, external specification for `std`/`core`/`alloc`, or verifier rlimit is changed.

## High

None.

## Medium

None.

## Low

None.

## Evidence check record

- **Exact-result API contract:** `after/ostd/src/mm/kspace/kvirt_area.rs:370-375` adds `returns self.range` to `KVirtArea::range`, and the body still returns `self.range.start..self.range.end`. This follows `use-returns-for-exact-results` and gives callers the equality needed to reason about the returned range.
- **Invariant-preserving API contract:** `after/ostd/src/mm/kspace/kvirt_area.rs:469-472` adds `final(regions).inv()` and `res.inv()` to `map_frames`. The former matches the existing `old(regions).inv()` precondition at line 445; the latter is supported by `KVirtArea::inv` at lines 305-320 and the allocator bounds supplied by `kvirt_alloc_range_bounds` at lines 226-253.
- **Trust boundary:** The removed `assume(range.end > 0)` is replaced by the allocator fact `KERNEL_BASE_VADDR <= range.start <= range.end` plus the computed constant fact `KERNEL_BASE_VADDR > 0` (`after/ostd/src/mm/kspace/kvirt_area.rs:488-491`). This reduces, rather than expands, trusted reasoning.
- **Deleted proof scaffolding:** The initial remaining-frame slot property is already stated as a `map_frames` precondition at lines 464-468, and its loop form remains explicit at lines 557-565. The later preservation block remains tied to `cursor.map`'s strengthened guarantees in the adjacent comment at lines 614-618. Static inspection found no changed executable statement or weakened obligation caused by deleting the two explicit quantified proof blocks.
- **Assumptions and invariants:** No new `assume`, `admit`, `external_body`, axiom, or unsafe operation is introduced by the patch. The existing allocator axiom and unsafe mapping call are unchanged.
- **Workflow checks:** `diff.patch` contains no `#[verifier::rlimit(...)]`, so there is no rlimit above 200. It adds or changes no external specification for a `std`, `core`, or `alloc` API, so the upstream-spec-reuse check is not triggered.
- **No-verification disclosure:** Per the fast-review override, no Verus run, compilation, tests, history inspection, exhaustive guideline enumeration, or isolated caller experiment was performed. Conclusions are based only on the authoritative patch and static before/after context; proof acceptance and CI status were not independently verified.
