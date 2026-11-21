# Review: PR #390 snapshot `ff234245b17b`

> Fast isolated review of the supplied `diff.patch`, using `before/` and `after/` only for line-level context. The review covers maintainability, proof/trust boundaries, assumptions, API contracts, invariants, specification reuse, and changed `rlimit`/external-spec workflow triggers.

**Bottom line:** This snapshot must not merge. The DMA implementation has several direct runtime regressions: platform detection now panics, IOMMU/TDX mapping work is gone, the overlap registry does not insert anything, and every permitted DMA read/write ends in `InvalidArgs`. In parallel, the patch replaces checked ownership transformations with `external_body` functions returning arbitrary tracked memory views, so the verification story no longer establishes exclusive ownership of the memory being accessed.

## High

### DMA platform detection and device mapping were replaced by stubs

- **Guideline:** `preserve-exec-code`
- **Location:** `ostd/src/mm/dma/mod.rs:131`; `ostd/src/mm/dma/dma_stream.rs:152`
- **Evidence:** The new detector is `#[verifier::external_body] pub fn dma_type() -> DmaType { unimplemented!() }`. In the new `DmaType::Iommu` branch, the loop computes `paddr` but the former `iommu::map(paddr as Daddr, paddr).unwrap()` call is only represented by the comment `// iommu::map...`. The base implementation queried `has_dma_remapping()`, performed the IOMMU map, and performed the x86 TDX unprotect operation.
- **Problem:** Every call to `DmaStream::map` reaches `dma_type()` and panics at runtime. Even after replacing that panic, both the IOMMU mapping and the TDX transition have been removed, so the returned device address does not denote the mapping promised by the API.
- **Suggestion:** Restore the original executable detector and both architecture-specific mapping paths unchanged, then specify those operations at their existing boundaries. If a specific call cannot yet be verified, retain the working executable call and isolate only its specification/trust obligation; do not replace runtime behavior with `unimplemented!()` or comments.

### The DMA overlap registry no longer records mappings

- **Guideline:** `preserve-exec-code`
- **Location:** `ostd/src/mm/dma/mod.rs:89`
- **Evidence:** The second loop computes `let paddr = ...`, but `mapping_set.insert(paddr)` is commented out at lines 121-122, after which the function returns `true`. The base implementation inserted every address. The patch also removes `remove_dma_mapping` and the `Drop for DmaStreamInner` implementation that released the registered range and tore down the device mapping.
- **Problem:** Two live streams over the same physical frames can both pass `check_and_insert_dma_mapping`, contradicting the documented `AlreadyMapped` behavior and the exclusivity invariant this set is meant to enforce. Removing teardown also loses the lifecycle symmetry needed once insertion is restored.
- **Suggestion:** Keep the original insert/remove and `Drop` behavior executable. Add the ghost model needed to prove that a successful insertion reserves the whole page range until the final inner owner is dropped, without deleting either side of the runtime lifecycle.

### All permitted DMA reads and writes now fail

- **Guideline:** `preserve-exec-code`, `api-postconditions`
- **Location:** `ostd/src/mm/dma/dma_stream.rs:343`; `ostd/src/mm/dma/dma_stream.rs:371`
- **Evidence:** After the direction and bounds checks, `read_inner_vmio` unconditionally executes `Err(Error::InvalidArgs)` at line 359, and `write_inner_vmio` does the same at line 387. The base implementation delegated valid operations to `self.inner.segment.read(offset, writer)` and `.write(offset, reader)`.
- **Problem:** The `VmIo` implementation cannot perform any successful transfer, including valid in-range operations in the permitted direction. This directly contradicts the trait documentation's read/write purpose and its no-short-success behavior.
- **Suggestion:** Restore delegation to the segment after the direction checks (and preserve the original offset semantics). Give the helper and trait implementation postconditions that state the success case's cursor/owner updates and error case's frame conditions.

### Trusted functions can fabricate memory-view ownership from shared metadata

- **Guideline:** `centralize-trusted-boundaries`, `complete-external-contracts`
- **Location:** `ostd/src/mm/frame/segment.rs:172`; `ostd/src/mm/frame/segment.rs:188`; `ostd/src/mm/io.rs:413`
- **Evidence:** `produce_kernel_mem_view` takes only `tracked &self` and returns an owned `tracked view: MemView` from `arbitrary()`; it can therefore be called repeatedly from the same shared `SegmentOwner`. `borrow_kernel_mem_view` likewise returns an arbitrary tracked reference. Separately, `VmIoOwner::advance` was changed from a checked `MemView::split`/`borrow_at` implementation to `#[verifier::external_body] ... { arbitrary() }`, and its `res` does not occur in any `ensures` clause despite the documentation claiming it is the advanced portion.
- **Problem:** These are local, generic trust boundaries for the memory permission that justifies reads and writes. In particular, a shared `&SegmentOwner` can manufacture multiple owned views of the same segment, while `advance` can return an unrelated tracked view; the contracts do not encode a transfer, split, or borrow relationship that prevents aliasing of write authority.
- **Suggestion:** Restore the checked `advance` implementation and specify `res` as precisely the removed prefix. Derive segment views from the actual frame-content ownership: consume or mutably split ownership for a writable view, and tie a read borrow's lifetime and model to the source owner. If an unavoidable architecture axiom remains, centralize the narrow external specification in the established external-spec boundary rather than exposing generic `external_body` constructors in `ostd/src`.

## Medium

### `VmIo`'s enabled DMA contract does not constrain any observable output

- **Guideline:** `api-postconditions`
- **Location:** `ostd/src/mm/dma/dma_stream.rs:424`; `ostd/src/mm/dma/dma_stream.rs:458`; `ostd/src/mm/io.rs:1075`
- **Evidence:** The implementation sets both `obeys_vmio_read_spec()` and `obeys_vmio_write_spec()` to `true`, but its `read_spec` and `write_spec` bodies are only `self.inv()`. `DmaStream::inv()` itself is `true` at lines 94-97. Thus the trait `ensures` at `io.rs:1090-1101` and `io.rs:1126-1137` says nothing about `r`, the final reader/writer, either final `VmIoOwner`, or the final stream owner.
- **Problem:** Even after the runtime bodies are repaired, verified callers cannot establish that success transfers all bytes, advances the cursor, updates the memory view, or that failure preserves inputs. The contract therefore fails to expose the trait's documented no-short-read/no-short-write semantics.
- **Suggestion:** Define `read_spec`/`write_spec` over all output positions. At minimum, pin success to full cursor advancement and the corresponding owner/view update, pin failure to the intended frame condition, preserve both owners' invariants and relationships, and connect direction/range failures to the returned error where the API promises those cases.

## Low

No low-severity findings.

## Evidence check record

- Treated `diff.patch` (5,150 lines, 40 changed paths) as authoritative and used numbered `before/` and `after/` sources to refute or confirm candidate findings.
- Confirmed the deleted executable behavior directly in `before/ostd/src/mm/dma/{mod.rs,dma_stream.rs}`: runtime DMA-type detection, mapping insertion/removal, IOMMU mapping, TDX transitions, `Drop` teardown, and segment I/O delegation were present there.
- Confirmed that the prior `VmIoOwner::advance` proof split or borrowed the existing `MemView`; the patch deletes that body and adds `external_body` plus `arbitrary()` without a postcondition for `res`.
- Searched the authoritative patch for changed `#[verifier::rlimit(...)]` attributes and newly added or materially changed `std`/`core`/`alloc` external specifications. No such workflow trigger is present; existing `rlimit(400)` sites are unchanged context, so no `rlimit > 200` finding is attributed to this patch.
- Searched the supplied after-tree for uses and definitions of the new memory-view bridges and `VmIo` specs. No existing reusable checked bridge was found in this snapshot that would justify the new arbitrary constructors; the deleted checked `advance` implementation is the direct reusable implementation for that case.
- **No-verification disclosure:** Per the fast-review instruction, I did not run Verus, Rust builds/tests, isolated client experiments, repository history, or CI. The findings above are static, evidence-backed comparisons; compiler- or solver-dependent claims were intentionally omitted.
