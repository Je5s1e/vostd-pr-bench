# Review: PR 797 snapshot 07c694bbca2a

> Produced from the supplied `diff.patch` and its `before/` and `after/` source snapshots, using the VOSTD maintainability, proof-engineering, workflow, and API-contract review criteria.
> Scope: the authoritative patch changes `ostd/src/boot/memory_region.rs` and `ostd/src/boot/mod.rs`; surrounding snapshot source was used only for context.

**Bottom line:** The executable normalization change is accompanied by a substantial contract and contains no new trusted assumptions or `rlimit` increase. One caller-facing contract problem should be fixed before merge: the public postconditions hide all of their useful semantics behind closed predicates for which no public elimination lemmas exist, so verified callers cannot recover the partition, type-selection, or coalescing facts promised by the documentation.

## High

No high-severity findings.

## Medium

### The normalization result is specified through predicates that callers cannot use

- **Guideline:** `api-postconditions`
- **Location:** `ostd/src/boot/memory_region.rs:358`
- **Evidence:** The result contract promises `is_partition(ret@, ...)`, `preserves_types(ret@, self.aligned_regions())`, and `coalesced(ret@)` at lines 567–572. Their definitions are all `pub closed spec fn` (lines 358, 392, and 401); `preserves_types` additionally delegates its meaning to the private, opaque `selected_type` at lines 380–388. The patch provides no public proof function that turns any of these abstract predicate facts into the documented element-level properties. Repository search in the supplied `after/` snapshot finds these predicates only in this file's contract and proof internals.
- **Problem:** Outside this module, a verified caller can retain the opaque predicate tokens but cannot derive the documented facts that regions are contiguous and aligned, that a particular output address has the most restrictive covering input type, or that adjacent regions differ in type. This leaves the main public API's postcondition insufficient for its natural callers even though the implementation proves the stronger facts internally.
- **Suggestion:** Export a small public lemma interface for each abstract predicate (for example, partition bounds/adjacency, selected type at a covered address, and adjacent-type inequality), with contracts stated through public accessors. Alternatively, expose suitably `open` public definitions where representation visibility permits. Keep `selected_type` private only if a public lemma fully exposes the caller-relevant consequence of `preserves_types`.

## Low

No low-severity findings.

## Evidence check record

- Read all 924 lines of `diff.patch` and compared the changed regions with `before/ostd/src/boot/memory_region.rs`, `after/ostd/src/boot/memory_region.rs`, and the changed boot module.
- Checked the new public executable APIs and normalization contract, the type invariant, alignment model, loop-bound argument, proof helper, and surrounding architecture address facts. In particular, `MAX_PADDR` is constrained below the linear-mapping span, so the `module` contract's translated-end bound also prevents the slice from crossing `VMALLOC_BASE_VADDR`.
- Searched the authoritative patch for `assume`, `admit`, `external_body`, axioms, and `#[verifier::rlimit(...)]`; none were introduced. No changed `std`/`core`/`alloc` external specification was present, so the upstream-spec workflow check was not triggered.
- Searched the supplied `after/` tree for consumers and eliminators of `is_partition`, `preserves_types`, and `coalesced`; there are no public consumer lemmas, and all uses are confined to the defining file.
- Per the fast-review instruction, no history inspection, Verus run, build, test, exhaustive rule pass, or isolated caller experiment was performed. Findings are therefore based on static source evidence only; verification/CI status was not independently checked.
