# Review: PR 65 snapshot (`diff.patch`)

> Fast, non-exhaustive VOSTD review of the supplied before/after snapshot.
> Scope: `pr-65-625495f69559/diff.patch` and the corresponding files under `before/` and `after/`; maintainability, proof/trust boundaries, assumptions, API contracts, invariants, `rlimit > 200`, and specification reuse.

**Bottom line:** The new trusted `allocate_pt` contract is unsound as written: it accepts unconstrained ghost identity inputs and then returns a well-formed node whose invariant proves those inputs valid. The same contract also fails to connect its `level` input to the allocated node, so it does not expose the fact needed by the newly verified insertion path. No `rlimit > 200` change or new reusable `std`/`core`/`alloc` specification appears in the patch.

## High

### H1 — `allocate_pt` manufactures validity for unconstrained inputs

- **Guideline:** `complete-external-contracts`
- **Location:** `lock-protocol/src/exec/rw/frame/mod.rs:19`
- **Evidence:** The changed trusted API has only `requires 1 <= level < 4`, but accepts `inst: Tracked<SpecInstance>` and `nid: Ghost<NodeId>` and ensures `res.wf(mem)`, `res.inst@.cpu_num() == GLOBAL_CPU_NUM`, `res.inst@.id() == inst@.id()`, and `res.nid@ == nid@` (`frame/mod.rs:19-33`). `PageTableNode::wf` includes `NodeHelper::valid_nid(self.nid@)` and `self.inst@.cpu_num() == GLOBAL_CPU_NUM` (`node/mod.rs:94-101`).
- **Problem:** Because this is an `#[verifier::external_body]`, a caller can supply an arbitrary `nid` and derive `NodeHelper::valid_nid(nid@)` from the identity postcondition plus `res.wf(mem)`. The contract similarly claims the global-CPU property without requiring it of the supplied instance. The current caller has these facts, but the public trusted boundary does not require them, so other callers can introduce unsupported proof facts independently of the implementation.
- **Suggestion:** Add `inst@.cpu_num() == GLOBAL_CPU_NUM` and `NodeHelper::valid_nid(nid@)` to `requires`, together with every other premise needed to construct `res.wf(mem)`. Keep the identity postconditions only after those premises are explicit, or narrow the API and derive the identity inputs from an already-valid parent abstraction.

## Medium

### M1 — The allocator does not promise the requested level

- **Guideline:** `api-postconditions`
- **Location:** `lock-protocol/src/exec/rw/frame/mod.rs:19`
- **Evidence:** `allocate_pt(level, ...)` requires `1 <= level < 4`, but none of its postconditions mentions `level` (`frame/mod.rs:25-33`). The new caller invokes it with `level - 1`, constructs `Child::PageTable`, and calls `entry.replace` (`cursor.rs:428-440`). That API now requires `new_child.wf_with_node(...)` (`node/entry.rs:80-87`), whose page-table arm requires `node.level_spec() == (pt.level_spec() + 1) as PagingLevel` (`node/child.rs:65-71`). `res.wf(mem)` does not constrain `res.level_spec()` (`node/mod.rs:94-102`).
- **Problem:** The allocator's callable contract cannot establish that its result has the requested level, so it does not provide the parent/child level relationship required by the next natural API call. It also leaves the executable meaning of the `level` argument unspecified.
- **Suggestion:** If this is the allocator's intended behavior, add `res.level_spec() == level` to its postconditions and use that guarantee to discharge `new_child.wf_with_node` before `replace`.

## Low

| Finding | Guideline | Detail |
|---|---|---|
| L1 — stale panic/compatibility documentation | `document-verified-apis` | `lock-protocol/src/exec/rw/node/entry.rs:76-80` says `replace` panics for incompatibility and links to `Child::is_compatible`, but no such method exists in the supplied after-tree; the verified API instead excludes incompatible inputs through `new_child.wf_with_node(...)`. Update the rustdoc to describe the verified precondition and any remaining runtime panic behavior. |

## Evidence check record

- Read the complete supplied `diff.patch` and inspected the corresponding before/after definitions and callers for `allocate_pt`, `PageTableNode::wf`, `Child::wf_with_node`, `Child::wf_into_pte`, `Entry::replace`, the read/write PTE operations, and the PTE constructor trait.
- Checked H1 against the after-tree invariant: `PageTableNode::wf` explicitly contains both `NodeHelper::valid_nid(self.nid@)` and the global-CPU invariant, while `allocate_pt` has no corresponding input preconditions.
- Checked M1 against all `allocate_pt` postconditions and `PageTableNode::wf`; neither relates the returned node's level to the function's `level` parameter.
- The commented-out `new_pt` non-leaf postcondition was not reported: `lemma_page_table_entry_properties` still states a related non-leaf fact, and without verification an actual caller-visible failure was not established strongly enough for this fast review.
- No changed `#[verifier::rlimit(...)]` was found, and no newly added or materially changed external specification for a `std`, `core`, or `alloc` API appears in scope. No evidence-backed duplicate reusable specification was identified.
- **No-verification disclosure:** Per the requested fast-review override, no Verus run, isolated client experiment, history analysis, sub-agent/persona fan-out, or exhaustive guideline checklist was performed. Findings are based on the supplied patch and static before/after context only.
