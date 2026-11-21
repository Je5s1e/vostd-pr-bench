# Review: PR 500 snapshot e909aa15bb90

> Fast isolated VOSTD review of `diff.patch`, using the supplied `before/` and `after/` trees for context.
> Scope: 17 changed files in `pr-500-e909aa15bb90/diff.patch`; maintainability, proof/trust boundaries, assumptions, API contracts, invariants, rlimit values above 200, and spec reuse.

**Bottom line:** The proof-side rename and module consolidation are mostly mechanical, and the patch adds no assumptions, admits, axioms, external bodies, or rlimit increases. One API-shape regression should be fixed before merge: `frame_to_index` and `index_to_frame` cease to be executable helpers and become spec-only functions, even though `frame_to_index` remains publicly re-exported as if it were the same caller-facing API.

## High

None.

## Medium

### Preserve the executable frame/index conversion API

- **Guidelines:** `preserve-exec-code`, `pair-exec-helpers-with-spec-models`
- **Location:** `ostd/specs/mm/frame/mapping.rs:63` (with the public re-export at `ostd/src/mm/frame/mod.rs:66`)
- **Evidence:** Before the patch, the model and executable API were explicitly paired:

  ```rust
  pub open spec fn frame_to_index_spec(paddr: Paddr) -> usize { ... }

  #[verifier::when_used_as_spec(frame_to_index_spec)]
  pub fn frame_to_index(paddr: Paddr) -> (res: usize)
      requires paddr % PAGE_SIZE == 0,
      ensures res == frame_to_index_spec(paddr),
  { ... }
  ```

  The patch replaces that pair with:

  ```rust
  pub open spec fn frame_to_index(paddr: Paddr) -> usize
      recommends paddr % PAGE_SIZE == 0,
  { ... }
  ```

  It makes the same executable-to-spec-only change to `index_to_frame`, while `ostd/src/mm/frame/mod.rs` still says `pub use meta::mapping::{..., frame_to_index, ...};`.
- **Problem:** This is not merely a proof rename. An executable public function is erased and replaced by a ghost/spec function under the same name, so existing executable callers of the re-exported `mm::frame::frame_to_index` no longer have the API they previously compiled against. That conflicts with the instruction to preserve caller-facing API shapes and with the rule to keep executable helpers paired with faithful spec models.
- **Suggestion:** Keep the executable `frame_to_index` and `index_to_frame` functions and their contracts. Preserve separate spec twins (the existing `_spec` names are sufficient), connected with `#[verifier::when_used_as_spec(...)]`; alternatively, use an established dual-spec mechanism only if it preserves the same executable signatures and public paths. The module consolidation can remain independent of this fix.

## Low

None.

## Evidence check record

- Read the complete 2,513-line `diff.patch` and compared the affected conversion module and call sites against the supplied `before/` and `after/` trees.
- The widespread `frame_to_index_spec`/`index_to_frame_spec` call-site edits are otherwise mechanical; executable in-tree uses converted to spec calls were changed to ghost bindings where necessary.
- Static search found no added `assume`, `admit`, `axiom`, `external_body`, or `#[verifier::rlimit(...)]` line. No rlimit above 200 was introduced, and no new or materially changed external specification for a `std`, `core`, or `alloc` API was present.
- The moved broadcast lemma and page/meta conversion contracts retain their prior logical conditions; no new trust boundary was identified in the reviewed diff.
- **No-verification disclosure:** Per the fast-review constraint, no Verus run, build, test, history inspection, isolated caller experiment, or exhaustive guideline pass was performed. Findings and clean checks above are based on static patch and before/after evidence only.
