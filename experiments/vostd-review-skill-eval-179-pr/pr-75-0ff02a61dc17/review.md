# Review: PR 75 snapshot `0ff02a61dc17`

> Fast, non-exhaustive VOSTD review of `diff.patch`, with the supplied `before/` and `after/` trees used for surrounding context.
> Scope: the 124-line deletion in `lock-protocol/src/spec/sub_page_table.rs` represented by `/Users/chao/workspace/REvolve/vostd-pr-test/pr-75-0ff02a61dc17/diff.patch`.

**Bottom line:** The change removes an unused prototype/test block, including two local `external_body` functions and `Tracked::assume_new()` calls, so it reduces rather than expands the trusted surface. No high- or medium-severity maintainability, proof/trust, assumption, invariant, API-contract, rlimit, or specification-reuse issue was found. The deletion does leave several imports and lint suppressions that served only the removed block.

## High

None.

## Medium

None.

## Low

| Finding | Guideline | Detail |
|---|---|---|
| Remove imports and suppressions orphaned by the deleted prototype | `organize-proof-imports`, `narrow-lint-suppressions` | `lock-protocol/src/spec/sub_page_table.rs:6-18,28` still contains `use std::collections::HashMap;`, `use vstd::hash_map::*;`, `use vstd::tokens::MapToken;`, `use vstd::raw_ptr::*;`, `use vstd::simple_pptr::*;`, `use vstd::simple_pptr::PointsTo;`, and `use crate::exec::SIZEOF_FRAME;`, plus three `#[allow(unused_imports)]` attributes. Identifier searches in the complete after-file find `HashMap`, `MapToken`, `PointsTo`, and `SIZEOF_FRAME` only on those import lines; the removed block was their only consumer. Delete the orphaned imports and their now-unnecessary suppressions (and similarly remove the unused glob imports after confirming their exported names are not needed by macro expansion). |

## Evidence check record

- Read all 124 lines of `diff.patch`; the only changed path is `lock-protocol/src/spec/sub_page_table.rs`, and the patch only deletes lines 328-446 from the before-file.
- Read the complete after-file and the corresponding before-file context. The deleted code contained the only occurrences of `alloc_page_table_entries`, `get_from_index`, `index_to_addr`, `addr_to_index`, `PHYSICAL_BASE_ADDRESS_SPEC`, `PHYSICAL_BASE_ADDRESS`, and `print_mem` in the supplied trees.
- Trust/assumption check: the deletion removes two `#[verifier::external_body]` helpers using `Tracked::assume_new()`, plus an `external_body` allocator wrapper and an `external_body` print helper. No replacement assumption, axiom, external body, or contract was added.
- API/invariant check: no surviving API signature, state-machine transition, invariant, `requires`, or `ensures` clause changes in the patch. Repository-wide searches of the supplied after-tree found no callers of the deleted helper names.
- Workflow check: the patch adds or changes no `#[verifier::rlimit(...)]` and adds or materially changes no external specification for a `std`, `core`, or `alloc` API. The `rlimit > 200` and upstream-specification checks therefore do not trigger.
- Specification-reuse check: the patch introduces no specification, proof helper, model, or external specification to compare for reuse.
- No-verification disclosure: per the requested fast-review constraints, I did not run Verus, Rust compilation, CI, history inspection, exhaustive guideline enumeration, or isolated caller/contract experiments. Conclusions are based on static inspection of the supplied patch and before/after source snapshots only.
