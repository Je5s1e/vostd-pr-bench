# Review: PR 500 isolated patch

> Scope: `diff.patch`, checked against the supplied `before/` and `after/` trees. The patch changes `ostd/specs/mm/frame/mapping.rs`, `ostd/src/mm/frame/meta.rs`, and deletes `ostd/src/mm/frame/meta/mapping.rs`.

**Bottom line:** No evidence-backed findings were identified. The change removes the duplicate frame-mapping implementation while preserving the established `crate::mm::frame::meta::mapping` path through a public re-export, and the canonical API retains the same relevant preconditions and postconditions. The added injectivity lemma states the needed aligned-address condition directly and introduces no new trust assumption.

## High

None.

## Medium

None.

## Low

None.

## Evidence check record

- Compared the complete `diff.patch` with both affected mapping implementations and their surrounding modules in the supplied `before/` and `after/` trees.
- Confirmed that `ostd/src/mm/frame/meta.rs:27` publicly re-exports `crate::specs::mm::frame::mapping`, preserving existing imports such as `crate::mm::frame::meta::mapping::{...}` after deletion of the duplicate module.
- Compared the deleted implementation with `ostd/specs/mm/frame/mapping.rs`. The canonical functions preserve the operational arithmetic and relevant contracts for `frame_to_index`, `index_to_frame`, `frame_to_meta`, and `meta_to_frame`; the canonical version also ties the frame-to-metadata specification to `meta_slot_size()` and includes `size_of_meta_slot` in `group_page_meta`.
- Checked the new `lemma_frame_to_index_injective` at `ostd/specs/mm/frame/mapping.rs:85-93`: its assumptions require both addresses to be page-aligned and distinct, and its conclusion is the corresponding inequality of their page indices. It is a proof lemma with an empty verified body, not an axiom, `assume`, or `admit`.
- Searched the scoped patch for verifier resource-limit changes, new trust primitives, and external `std`, `core`, or `alloc` specifications. None are present; in particular, there is no `#[verifier::rlimit(...)]` change above the workflow threshold of 200.
- Checked repository-wide supplied after-tree references to both mapping paths and to `group_page_meta`; the compatibility re-export covers the legacy path while the canonical specs path remains available.
- Per the fast-review override, no Verus run, build, test, history inspection, exhaustive guideline pass, or isolated caller experiment was performed. Conclusions are based on static source and patch evidence only.
