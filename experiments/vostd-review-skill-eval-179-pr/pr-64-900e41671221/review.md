# Review: PR 64 snapshot (`diff.patch`)

> Fast, non-exhaustive VOSTD review of the supplied before/after snapshot.
> Scope: `pr-64-900e41671221/diff.patch` and the corresponding files under `before/` and `after/`; maintainability, proof/trust boundaries, assumptions, API contracts, invariants, `rlimit > 200`, and specification reuse.

**Bottom line:** The new trusted `allocate_pt` contract is unsound as written: it accepts unconstrained ghost identity inputs and then returns a well-formed node whose invariant proves those inputs valid. The same contract also fails to connect its `level` input to the allocated node, so it does not expose the fact needed by the newly verified insertion path. No `rlimit > 200` change or new reusable `std`/`core`/`alloc` specification appears in the patch.

## High

### H1 — `allocate_pt` manufactures validity for unconstrained inputs

- **Guideline:** `complete-external-contracts`
- **Location:** `lock-protocol/src/exec/rw/frame/mod.rs:19`
- **Evidence:** The changed trusted API has only `requires 1 <= level < 4`, but accepts `inst: Tracked<SpecInstance>` and `nid: Ghost<NodeId>` and ensures both `res.wf(mem)`, `res.inst@.id() == inst@.id()`, and `res.nid@ == nid@` (`frame/mod.rs:19-32`). `PageTableNode::wf` includes `NodeHelper::valid_nid(self.nid@)` and `self.inst@.cpu_num() == GLOBAL_CPU_NUM` (`node/mod.rs:94-101`). The contract additionally states `res.inst@.cpu_num() == GLOBAL_CPU_NUM` directly.
- **Problem:** Because this is an `#[verifier::external_body]`, a caller can supply an arbitrary `nid` (and any obtainable instance token) and derive `NodeHelper::valid_nid(nid@)` and the global-CPU property without proving either at the call site. The current caller happens to have those facts, but the public trusted contract does not require them, so the boundary can introduce false proof facts independently of the implementation.
- **Suggestion:** Add `inst@.cpu_num() == GLOBAL_CPU_NUM` and `NodeHelper::valid_nid(nid@)` to `requires` (plus every other condition the allocator needs to construct `res.wf(mem)`). Keep the identity postconditions only after those premises are explicit, or narrow the function's visibility and derive the identity inputs from an already-valid parent abstraction.

## Medium

### M1 — The allocator does not promise that it allocated the requested level

- **Guideline:** `api-postconditions`
- **Location:** `lock-protocol/src/exec/rw/frame/mod.rs:19`
- **Evidence:** `allocate_pt(level, ...)` requires `1 <= level < 4`, but none of its postconditions mentions `level` (`frame/mod.rs:25-32`). The new caller invokes it with `level - 1` (`cursor.rs:428-433`), constructs a `Child::PageTable`, and immediately calls `entry.replace` (`cursor.rs:436-444`). That API now requires `new_child.wf_with_node(...)` (`node/entry.rs:80-87`), whose page-table arm requires `node.level_spec() == (pt.level_spec() + 1) as PagingLevel` (`node/child.rs:62-71`). `res.wf(mem)` does not constrain `res.level_spec()` (`node/mod.rs:94-102`).
- **Problem:** The trusted allocator's callable contract cannot establish that its result has the requested level, so the natural next call cannot derive the newly required parent/child level relationship from this API. This also leaves the executable meaning of the `level` argument unspecified.
- **Suggestion:** Add `res.level_spec() == level` to `allocate_pt`'s postconditions, provided that is the allocator's intended behavior, and use it to discharge `new_child.wf_with_node` before `replace`.

## Low

| Finding | Guideline | Detail |
|---|---|---|
| L1 — stale panic/compatibility documentation | `document-verified-apis` | `node/entry.rs:76-80` says `replace` panics for incompatibility and links to `Child::is_compatible`, but no such method exists in the supplied after-tree and the verified API instead excludes incompatible inputs through `new_child.wf_with_node(...)`. Update the rustdoc to describe the verified precondition and remaining trusted/runtime behavior; do not claim a panic path the body does not implement. |

## Evidence check record

- Read the complete supplied `diff.patch` and inspected the corresponding before/after definitions and callers for `allocate_pt`, `PageTableNode::wf`, `Child::wf_with_node`, `Child::wf_into_pte`, `Entry::replace`, and the PTE constructor trait.
- Attempted to refute H1 by checking whether `PageTableNode::wf` omitted the relevant validity facts; it explicitly contains both `NodeHelper::valid_nid(self.nid@)` and the global-CPU invariant, so the finding is confirmed by static contract composition.
- Attempted to refute M1 by checking whether `PageTableNode::wf` or another `allocate_pt` postcondition related the result level to the input; no such relation is present in the supplied after-tree.
- The commented-out `new_pt` non-leaf postcondition was not reported: `lemma_page_table_entry_properties` still states a related non-leaf fact, and without verification an actual caller-visible failure was not established strongly enough for this fast review.
- No `#[verifier::rlimit(...)]` change and no newly added/materially changed external specification for a `std`, `core`, or `alloc` API was found. No duplicate reusable specification was identified in scope.
- **No-verification disclosure:** Per the requested fast-review override, no Verus run, isolated client experiment, history analysis, or exhaustive guideline checklist was performed. Findings are based on the immutable supplied patch and static before/after context only.
