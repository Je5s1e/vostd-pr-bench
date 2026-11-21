# Review: PR 500 isolated patch

> Produced from the VOSTD review skill's maintainability, proof-engineering, and API-contract criteria.
> Scope: fast, non-exhaustive static review of `diff.patch`, with `before/` and `after/` used only for surrounding context.

**Bottom line:** The patch largely performs a consistent rename of the frame-index specification API, but the relocation of the executable address conversions introduces a second pair of specifications for arithmetic that already has canonical models under `ostd/specs/`. That duplication should be removed before merge so executable contracts and the existing page-metadata lemmas cannot drift apart. No high-severity issue was found in this limited review.

## High

None.

## Medium

### Reuse the canonical frame/metadata conversion specifications

- **Guideline:** `reuse-existing-specifications`
- **Location:** `ostd/src/mm/frame/meta.rs:42`
- **Evidence:** The patch adds local models:

  ```rust
  pub open spec fn frame_to_meta_local_spec(paddr: Paddr) -> Vaddr {
      (FRAME_METADATA_RANGE.start + (paddr / PAGE_SIZE) * meta_slot_size()) as usize
  }

  pub open spec fn meta_to_frame_local_spec(vaddr: Vaddr) -> Paddr {
      ((vaddr - FRAME_METADATA_RANGE.start) / META_SLOT_SIZE as int * PAGE_SIZE) as usize
  }
  ```

  while the canonical specification module still defines the same models at `ostd/specs/mm/frame/mapping.rs:45` and `:54`:

  ```rust
  pub open spec fn frame_to_meta_spec(paddr: Paddr) -> (res: Vaddr) { ... }
  pub open spec fn meta_to_frame_spec(vaddr: Vaddr) -> Paddr { ... }
  ```

  The new executable wrappers then use `#[verifier::when_used_as_spec(frame_to_meta_local_spec)]` and `#[verifier::when_used_as_spec(meta_to_frame_local_spec)]`, whereas the existing bijection and soundness lemmas continue to state their results over `frame_to_meta_spec` and `meta_to_frame_spec` (`ostd/specs/mm/frame/mapping.rs:89-137`).
- **Problem:** The executable APIs and the reusable proof lemmas now speak through independently declared copies of the same mathematical conversions. Even though their current bodies are arithmetically equivalent, either copy can change without its contract forcing the other to change, creating avoidable model drift and extra unfolding obligations at callers.
- **Suggestion:** Make the executable wrappers' `when_used_as_spec` targets the canonical functions from `ostd/specs/mm/frame/mapping.rs` (using an imported alias if the attribute requires an unqualified identifier), and remove both `*_local_spec` definitions. Keep a separate local model only if the toolchain cannot reference the canonical model here, and in that case add and use an explicit equivalence lemma so the wrapper contract is connected to the canonical API.

## Low

None.

## Evidence check record

- Read the complete authoritative `diff.patch` (2,695 lines) and inspected the corresponding `before/` and `after/` definitions around every materially changed frame-mapping API.
- Searched the isolated `after/` tree for the removed `frame_to_index_spec` and `index_to_frame_spec` names; no stale occurrences were found.
- Compared the new local conversion models and wrapper contracts with the canonical models and all page-metadata bijection/soundness lemmas in `ostd/specs/mm/frame/mapping.rs`.
- Searched the authoritative patch for added or changed `#[verifier::rlimit(...)]` attributes; none were present, so the workflow `rlimit > 200` check was not triggered.
- No new or materially changed external specification for a `std`, `core`, or `alloc` API was found, so the upstream-spec workflow check was not triggered.
- No targeted client experiment, Verus invocation, build, test, history inspection, or exhaustive guideline checklist was performed, as required by this fast-review scope. The isolated snapshot does not contain `docs/coding-guidelines`; review criteria came from the current `vostd-code-review` skill and its personas. Consequently, the finding is based on static source evidence only and verification status is unknown.
