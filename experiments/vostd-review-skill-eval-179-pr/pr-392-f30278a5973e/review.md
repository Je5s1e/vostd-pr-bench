# Review: `diff.patch` (`before` → `after` snapshot)

> Produced from the VOSTD coding guidelines and API-contract criteria.
> Scope: the 330-line `diff.patch`, with the corresponding `before/` and `after/` files used only for surrounding context.

**Bottom line:** No high-severity soundness or API-contract defect is established by this fast static review. Two maintainability issues should be fixed before merge: the patch rewrites executable paths without the required `Origin Rust:` record and introduces a public, single-use proof helper whose result already follows from the caller's invariants. No changed `#[verifier::rlimit(...)]`, new `assume`/`admit`/`external_body`, or materially changed reusable external specification for a `std`, `core`, or `alloc` API was found.

## High

None.

## Medium

### Preserve the original executable paths in the required reviewable form

- **Guideline:** `preserve-exec-code`
- **Locations:** `ostd/src/mm/frame/unique.rs:133`, `ostd/src/mm/kspace/kvirt_area.rs:450`
- **Evidence:** `UniqueFrame::repurpose` adds an anonymous block containing the former executable sequence, beginning `/* // SAFETY: We are the sole owner and the metadata is initialized.` and ending with `unsafe { core::mem::transmute(self) } */`. The mapping loop likewise adds only `// unsafe { cursor.map(MappedItem::Tracked(frame.into(), prop)) }` / `//     .expect("Failed to map frame in a new `KVirtArea`");`, while execution now goes through `let dynframe = frame_into_dynframe(frame);` and `cursor.map(item)`.
- **Problem:** These are real executable rewrites made for verification, but the preserved originals are not marked `Origin Rust:` and do not state the concrete reason for each rewrite. The VOSTD rule requires an adjacent, concise original-code record and reason so reviewers can check runtime equivalence.
- **Suggestion:** Replace each anonymous commented block with an adjacent `Origin Rust:` block that quotes the exact former executable statement(s) and briefly states the Verus constraint that required the rewrite (tracked metadata ownership for `repurpose`; exposing the conversion model before `cursor.map` for the mapping loop). Keep the rewritten executable path minimal.

### Inline the one-use invariant bridge instead of expanding the public proof API

- **Guidelines:** `inline-single-use-proof-helpers`, `name-proof-roles`
- **Location:** `ostd/specs/mm/frame/unique.rs:111`
- **Evidence:** The patch adds `pub proof fn aligns_with_regions(...)` with an empty body and postconditions equating the region's `inner_perms` and `self_addr` with the owner's fields. Repository search finds exactly one call, at `ostd/src/mm/frame/unique.rs:142`. Its key equalities are already stated by `owner.global_inv(regions)` at `ostd/specs/mm/frame/unique.rs:81-85`. The helper is also a proved reusable fact but is not named with the required `lemma_` prefix.
- **Problem:** This creates a public proof surface for a single local proof step and obscures that the conclusion is a direct consequence of the existing invariant (plus the frame/owner index equalities). The extra `regions.inv()` and unique-reference-count requirements do not contribute to the stated conclusion.
- **Suggestion:** Remove `aligns_with_regions` and prove/assert the index equality and the two `global_inv` conjuncts directly in `UniqueFrame::repurpose`. If a genuine second caller later establishes an abstraction need, reintroduce a narrowly contracted `lemma_*` fact with only the premises used by its conclusion.

## Low

| Finding | Guideline | Detail |
|---|---|---|
| Consolidate the newly duplicated module import at `ostd/specs/mm/frame/unique.rs:6-7`. | `group-imports-by-crate` | The file has both `use super::meta_owners::*;` and the added `use super::meta_owners::REF_COUNT_UNIQUE;`; the glob already brings the constant into scope. Remove the explicit duplicate (or replace the glob with one consolidated explicit import list if that is independently desirable). |

## Evidence check record

- Read `diff.patch` in full and inspected the affected `after/` sources with line numbers; compared relevant `before/` hunks through the patch.
- Searched the snapshot for callers of `aligns_with_regions` and `from_raw_owner`, and checked the definitions of `UniqueFrameOwner::inv`, `UniqueFrameOwner::global_inv`, `MetaSlot::inc_ref_count_panic_cond`, and the `Frame<M> -> UFrame` executable conversion.
- Checked the patch text for changed `#[verifier::rlimit(...)]`, `assume`, `admit`, and `external_body` additions. The patch removes admits but adds none of these trust mechanisms.
- Checked the newly added `FromSpecImpl<Frame<M>> for UFrame` against the executable `From<Frame<M>> for UFrame`: both preserve the frame pointer and change only the phantom metadata type, so this review found no evidence-backed contract mismatch.
- The added reference-count preconditions are consistent with the existing panic guard (`value() >= REF_COUNT_MAX`) and the model's legal shared-count range; no independent API-precondition finding is reported.
- Per the requested fast-review override, no Git history, exhaustive rule enumeration, Verus execution, CI verification, caller experiment, or targeted proof experiment was performed. Findings are based only on static patch and before/after context; successful verification is not claimed.
