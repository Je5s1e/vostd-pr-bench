# Review: PR #456 isolated patch

> Produced from the VOSTD coding-guideline criteria and API-contract checks.
> Scope: fast, non-exhaustive static review of `diff.patch` as the authoritative change, with the supplied `before/` and `after/` trees used only for context.

**Bottom line:** The patch publicly enables `DmaCoherent`, but the enabled implementation no longer performs the cache-policy, TDX, or IOMMU operations that make the mapping coherent and device-accessible, and it no longer tears down the mapping on drop. This is a blocking runtime regression, not merely unfinished proof work. The new verified public surface also has contracts too weak for callers and introduces local `external_body` trust boundaries.

## High

### The newly exported DMA mapping is operationally a placeholder

- **Guideline:** `preserve-exec-code`
- **Location:** `ostd/src/mm/dma/dma_coherent.rs:113` (also lines 128-134 and the missing former drop path); export at `ostd/src/mm/dma/mod.rs:2-3`
- **Evidence:** The patch changes `// mod dma_coherent;` into `mod dma_coherent; pub use dma_coherent::DmaCoherent;`, while the enabled constructor contains `// TODO: restore TDX GPA sharing once the arch hook is verified.` and `// TODO: restore iommu::map once the IOMMU API is verified.`; the IOMMU loop now only computes `let _paddr = ...` and increments `i`. It also stores but never uses `is_cache_coherent` (`// TODO: restore cache-policy switching...`). The prior context performed cache conversion, TDX sharing, and `iommu::map`, and its `Drop` implementation undid those operations and called `remove_dma_mapping`; the after-file has no `Drop` implementation even though lines 37-38 still promise, “The mapping will be destroyed automatically when the object is dropped.”
- **Problem:** `map` can return `Ok` without making non-coherent memory uncacheable, sharing TDX pages, or installing IOMMU entries. Dropping the result cannot unmap or remove the range from the software mapping registry, so later mappings can remain permanently rejected as `AlreadyMapped`; hardware and cache state are also not restored. Exporting this implementation makes the proof-driven executable rewrite visible to real callers with behavior that contradicts the type's purpose and documentation.
- **Suggestion:** Keep `dma_coherent` unexported until the executable behavior is complete, or restore the original cache-policy, TDX, IOMMU, and drop/registry-cleanup operations and specify those original callees at their boundaries. Do not replace hardware operations with no-op loops merely to bring the wrapper under verification.

## Medium

### Public constructor and getters do not expose their meaningful results

- **Guideline:** `api-postconditions`
- **Location:** `ostd/src/mm/dma/dma_coherent.rs:94` and `ostd/src/mm/dma/dma_coherent.rs:324`
- **Evidence:** `map` only ensures `r matches Ok(r) ==> r.inner.wf()` (lines 94-102), without relating a successful result to the supplied segment, its address/size, or the created device address. The deterministic public getters `daddr`, `paddr`, `nframes`, and `nbytes` (lines 324-369) ensure only `self.inner.wf()` and place no constraint on their return binder `r`, even though their private one-hop helpers have exact `returns` clauses (lines 150-190).
- **Problem:** Verified callers cannot learn what object a successful `map` created or use any exact result from the public getters. The implementation proves the values internally but discards those facts at the public API boundary, preventing natural address/size reasoning.
- **Suggestion:** Define a stable abstract view for `DmaCoherent`, relate successful `map` results to the input segment and selected device address, and give each deterministic getter an exact `returns` clause over that view. Avoid exposing locking or other incidental representation details.

### Core correctness depends on locally admitted method bodies

- **Guideline:** `centralize-trusted-boundaries`
- **Location:** `ostd/src/mm/dma/dma_coherent.rs:307` (also lines 701, 730, and 735)
- **Evidence:** `read_inner` is marked `#[verifier::external_body]` while promising the returned guard satisfies `r@.inv()`. `read_byte`, `read_once`, and `write_once` are likewise admitted in the implementation module. The verified getters and all `VmIo` read/write paths call `read_inner`, so its admitted postcondition is load-bearing for the rest of the proof.
- **Problem:** The patch creates multiple trusted facts beside their callers, including the guard invariant that unlocks access to the tracked segment ownership. This expands the trusted surface inside an ordinary implementation module and makes it difficult to audit whether the contracts match the underlying synchronization and I/O APIs.
- **Suggestion:** Verify these wrappers from the existing `RwArc`/`VmReader`/`VmWriter` contracts. If a tool or dependency gap genuinely requires trust, place the narrow external specification in the project’s centralized external-spec boundary, match the original signatures precisely, and document the concrete trusted assumption.

## Low

No low-severity findings.

## Evidence check record

- Read all 898 lines of `diff.patch`; treated it as authoritative.
- Compared the affected `before/` and `after/` files, especially constructor, I/O, destructor, export, and contract context.
- Static trust scan found four added `#[verifier::external_body]` sites and no added `assume`, `admit`, or axiom.
- No `#[verifier::rlimit(...)]` change appears in the patch, so there is no `rlimit > 200` finding.
- No new or materially changed external specification for a `std`, `core`, or `alloc` API appears in scope. No clear duplicated reusable spec/lemma was identified in this limited static pass.
- **No-verification disclosure:** Per the fast-review scope, no Verus run, build, test, history inspection, caller experiment, or exhaustive guideline sweep was performed. Findings are based on static patch and supplied before/after evidence only.
