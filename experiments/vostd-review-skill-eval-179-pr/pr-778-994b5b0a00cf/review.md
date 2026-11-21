# Review: PR 778 snapshot `994b5b0a00cf` (fast static review)

## Scope

Fast isolated review of the authoritative `diff.patch`, with the corresponding `before/` and `after/` trees used only for context. The review covers maintainability, proof/trust boundaries, assumptions, API contracts and invariants, `rlimit` values above 200, and reusable specifications. Per the requested fast-review override, it does not inspect history, exhaustively enumerate every guideline, run Verus, or run caller experiments.

**Bottom line:** One medium-severity API-contract issue remains. The new private alignment helper cannot be called for every valid usable memory region: its precondition rules out regions that contain no complete page, even though inward alignment has a natural empty result and the implementation can represent empty regions.

## High

None.

## Medium

### `as_aligned` unnecessarily excludes valid short usable regions

**Rule:** `api-preconditions` — make `requires` no stronger than soundness and the documented behavior require.

**Location:** `ostd/src/boot/memory_region.rs:207-225`, with the model at `ostd/specs/mm/frame/memory_region_specs.rs:59-68`.

**Problem:** The new contract requires

```rust
self@.typ == MemoryRegionType::Usable.to_int()
    ==> self@.align_inward().inv()
```

For a valid usable region that contains no complete page, inward rounding crosses the endpoints. For example, `MemoryRegion::new(1, 1, Usable)` satisfies `self.inv()`, but its modeled inward alignment has `base = 4096` and `end = 0`, so `align_inward().inv()` is false. Such input is consistent with the type's existing constructor and with the helper's stated purpose of excluding partially usable pages. The expected aligned region is simply empty; `MemoryRegion::is_empty` and the zero-length representation already support that outcome.

The executable body currently computes `end - base` at line 241, which explains the strengthened precondition but does not make it an API-level semantic restriction: it merely avoids the underflow caused by this implementation. This helper is also the alignment step used by the surrounding `into_non_overlapping` algorithm when that code is enabled, so requiring callers to prove that every usable bootloader region contains a full page is an avoidable obligation.

**Suggested correction:** Define inward alignment so crossed endpoints produce an empty region, for example by using `end.saturating_sub(base)` and modeling the aligned end as `max(aligned_base, align_down(old_end))` (or equivalently modeling the returned length directly). Then replace the derived `align_inward().inv()` requirement with only the genuine arithmetic bound needed by `align_up`, and state the sub-region guarantee conditionally for a nonempty result if necessary.

## Low

None.

## Evidence check record

- Read all 169 lines of `diff.patch` and checked both changed files against their `before/` and `after/` context.
- Confirmed `MemoryRegion::inv()` permits the concrete example: it requires only `base + len <= MAX_PADDR`; `MemoryRegion::new` exposes the same condition.
- Evaluated the new model definitions: `align_inward` rounds `base` up and `end` down, while `MemRegionModel::inv()` requires `base <= end`.
- Checked `align_ext::AlignExt`: `align_up` returns `nat_align_up`, `align_down` returns `nat_align_down`, and the current subtraction `end - base` is the implementation pressure behind the extra precondition.
- Checked the surrounding intended caller: `into_non_overlapping` maps every stored region through `as_aligned`, without a prior full-page-size filter.
- No changed `#[verifier::rlimit(...)]` was present, so there is no value above 200 to report.
- No new or materially changed external specification for a `std`, `core`, or `alloc` API was present.
- No new `assume`, `admit`, `external_body`, or other explicit trust escape was introduced.

## Verification disclosure

No Verus verification, build, test, history analysis, or isolated caller experiment was run, as required by the fast-review override. Findings are based on static inspection of the authoritative patch and supplied before/after source context.
