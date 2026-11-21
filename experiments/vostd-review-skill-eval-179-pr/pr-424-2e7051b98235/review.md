# Review: PR #424 captured patch

> Scope: fast, non-exhaustive static review of the authoritative `diff.patch` (11,549 lines, 40 changed files), with `before/` and `after/` consulted for line-level context. The review covers maintainability, proof/trust boundaries, assumptions, API contracts, invariants, changed `rlimit > 200`, and specification reuse.

**Bottom line:** The patch is not ready to merge. Its new frame-trackedness axiom can be instantiated on two valid owners that differ only in the unconstrained `is_tracked` argument, deriving both MMIO and non-MMIO for the same physical address. A cursor invariant is also restored by assuming the missing child invariant, while two safe APIs rely on explicit overflow assumptions; several proof functions additionally exceed the workflow's `rlimit` cap by up to two orders of magnitude.

## High

### H1 — The tracked/MMIO axiom is inconsistent with the unrestricted frame-owner constructor

- **Guideline:** `centralize-trusted-boundaries`
- **Location:** `ostd/specs/mm/page_table/node/entry_owners.rs:106`, `:124`, `:141`, `:777`
- **Evidence:** `new_frame(..., is_tracked: bool)` has no precondition and returns `Self::new_frame_spec(..., is_tracked)` (`:106-107`). `inv_base` constrains a frame's address, size, level, and shape but never constrains `frame.unwrap().is_tracked` (`:777-806`). Nevertheless, the new broadcast axiom promises for every frame satisfying `inv_base` that `entry.frame.unwrap().is_tracked != is_mmio_paddr(entry.frame.unwrap().mapped_pa)` (`:141-148`). The adjacent `axiom_frame_is_tracked_matches_item` similarly claims a relationship omitted from `inv_base`, and its comment explicitly says the invariant formulation was abandoned because it would require fixing call sites (`:120-123`).
- **Problem:** For any inputs satisfying the address/path/level shape requirements, `new_frame` can construct one `inv_base` owner with `is_tracked = true` and another with `is_tracked = false` at the same `paddr`. Applying `axiom_frame_is_tracked_iff_not_mmio` to both proves respectively `!is_mmio_paddr(paddr)` and `is_mmio_paddr(paddr)`. This makes the proof context inconsistent and allows downstream mapping and allocator-disjointness obligations to be proved from false.
- **Suggestion:** Make trackedness a checked structural invariant. Restrict the constructor with the required relationship (or derive `is_tracked` from the item/address instead of accepting an arbitrary boolean), add the relationship to `inv_base`, and discharge it at every construction and mutation site. Remove both global axioms; the comment's “wide cascading refactor” is the proof obligation, not a sound reason to assume the result.

### H2 — Child restoration assumes the exact page-table invariant it advertises as proved

- **Guideline:** `centralize-trusted-boundaries`
- **Location:** `ostd/specs/mm/page_table/cursor/owners.rs:393`, `:487`, `:499`
- **Evidence:** `continuation_inv_holds_after_child_restore` promises `self.inv()` (`:393-448`). To establish its `pt_inv_children` component, the new proof handles the restored index with `assume(PageTableOwner(self.children[cont_idx].unwrap()).pt_inv());` (`:487-500`). The preceding comment acknowledges that proving this requires fixing stale path propagation in `alloc_if_none` and adding an operation-specific lemma (`:489-492`).
- **Problem:** The assumption is not an environmental or hardware boundary; it is the missing inductive step for the page-table invariant. Every caller can now obtain `self.inv()` after restoring a child even when that child's paths do not satisfy `pt_inv`, so later verified cursor operations may rely on an invariant that was never established.
- **Suggestion:** Fix child-path propagation and prove an operation-specific `pt_inv` preservation lemma for each restore operation, then pass that proved fact into this helper. Do not expose `self.inv()` until the restored child case is checked, and do not keep the missing invariant as a local assumption.

## Medium

### M1 — Safe range operations hide executable overflow behind assumptions

- **Guideline:** `centralize-trusted-boundaries`
- **Location:** `ostd/src/mm/frame/segment.rs:878`, `:881`; `ostd/src/mm/vm_space.rs:852`, `:860`
- **Evidence:** Safe `Segment::slice` says `// KNOWN BUG` and assumes both `self.range.start + range.start <= usize::MAX` and the analogous end bound immediately before performing those additions (`segment.rs:878-886`). Safe `VmSpaceCursor::unmap` likewise assumes `self.pt_cursor.0.va + len <= usize::MAX` immediately before using that addition in an assertion and as `end_va` (`vm_space.rs:852-868`). Neither public contract requires the no-overflow condition; `slice_requires` only constrains frames selected by the resulting mathematical sums (`segment.rs:506-526`), and `unmap` only requires cursor and TLB invariants (`vm_space.rs:838-851`).
- **Problem:** These assumptions let verification ignore reachable arithmetic-overflow behavior in safe executable APIs and use the assumed sums to prove their postconditions. Labeling the condition a known bug identifies rather than justifies the new trusted premise.
- **Suggestion:** Establish the bound from existing cursor/segment invariants and the requested range, or express overflow through a checked addition and the API's documented panic behavior. If the intended caller invariant is genuinely required, add it explicitly to the contract and prove it at callers rather than assuming it inside the body.

### M2 — Five changed proof limits exceed the workflow cap

- **Guideline:** `decompose-before-raising-rlimit`
- **Location:** `ostd/specs/mm/page_table/mod.rs:443`; `ostd/specs/mm/page_table/cursor/owners.rs:1310`, `:1491`; `ostd/src/mm/page_table/cursor/mod.rs:730`, `:3309`
- **Evidence:** The patch adds or raises limits to `400`, `2000`, `20000`, `800`, and `10000`, respectively. All are greater than the permitted cap of `200`; `node_within_locked_range` is explicitly raised from `10000` to `20000`, and `replace_cur_entry` receives `10000`.
- **Problem:** These limits conceal proof-search blowups instead of decomposing the new arithmetic and cursor-preservation arguments. The largest caps are 50–100 times the workflow limit and make verification substantially less predictable and maintainable.
- **Suggestion:** Split the arithmetic normalization and invariant-preservation steps into focused lemmas, minimize broadcast/reveal scope, and keep each resulting proof at `rlimit <= 200` before merging.

## Low

None.

## Evidence check record

- Read the complete `diff.patch` and used the captured `after/` sources to resolve exact declarations, contracts, invariant definitions, and line numbers; `before/` was consulted to distinguish newly added or changed trust markers and limits.
- Refutation check for H1: `new_frame_spec` stores its boolean argument verbatim, `new_frame` has no precondition, and `inv_base` contains no trackedness/MMIO clause. Thus the two opposite-boolean instances are both admitted by the stated API whenever the common structural inputs are valid.
- Refutation check for H2: the assumed proposition is exactly the restored-index case of `pt_inv_children`; no earlier requirement supplies that child's `PageTableOwner(...).pt_inv()`, and the source comment identifies it as an unproved operation-specific obligation.
- Checked the safe API contracts around both overflow assumptions. Neither contract states the assumed no-overflow premise, and both bodies subsequently execute the corresponding additions.
- Compared changed `rlimit` annotations against the workflow's numeric cap. The report lists only changed limits above `200`; the added `60` and the changed `200` limit are not findings.
- Scanned additions for `assume`, `admit`, axioms, `external_body`, uninterpreted specifications, unsafe/trust comments, and external-specification markers. No separate strong `std`/`core`/`alloc` upstream-spec reuse finding was supported by the captured patch.
- **Verification disclosure:** Per the requested fast-review constraints, no sub-agents, commit history, exhaustive rule enumeration, Verus invocation, compilation, CI run, standalone proof experiment, or isolated caller experiment was performed. Findings rely on static evidence from the captured patch and before/after context only.
