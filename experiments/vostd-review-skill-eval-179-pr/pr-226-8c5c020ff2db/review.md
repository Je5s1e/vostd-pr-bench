# Review: PR 226 snapshot `8c5c020ff2db`

> Produced from the VOSTD coding-guideline criteria and the skill's API-contract criteria.
> Scope: fast, non-exhaustive static review of the changes recorded in `diff.patch`, using `before/` and `after/` only for surrounding context.

**Bottom line:** The patch is not merge-ready because it comments out the boot module's runtime API and nearly the entire `MemoryRegionArray` implementation while existing architecture and memory-management code still calls those items. The new `MemoryRegion` verification also omits the documented page-alignment validity condition, and the new array model has no intrinsic invariant tying its sequence, count, and capacity together. These should be corrected before proof work is integrated.

## High

### Verification work removes the executable boot path

- **Guideline:** `preserve-exec-code`
- **Location:** `ostd/src/boot/mod.rs:8`, `ostd/src/boot/mod.rs:10`, `ostd/src/boot/memory_region.rs:127`, `ostd/src/boot/memory_region.rs:200`, `ostd/src/boot/memory_region.rs:237`
- **Evidence:** The patch changes `pub mod smp;` to `//pub mod smp;`, starts a block comment before the boot API (`/*` at line 10), block-comments `MemoryRegion::{kernel, framebuffer, module, as_aligned}`, and starts another block comment immediately before every `MemoryRegionArray` implementation. Existing source still contains calls such as `MemoryRegionArray::new()` (`ostd/src/arch/x86/boot/linux_boot/mod.rs:130`), `MemoryRegion::framebuffer(&fb)` (line 146), `MemoryRegion::kernel()` (line 150), `MemoryRegion::module(initramfs)` (line 154), and imports `call_ostd_main`, `EarlyBootInfo`, and `EARLY_INFO` (line 199).
- **Problem:** This is not a behavior-preserving verification change: it deletes the executable API from the compiled crate and leaves live callers referring to missing functions, types, and statics. It also removes the boot initialization/entry path rather than verifying it incrementally.
- **Suggestion:** Restore all original executable declarations and implementations verbatim. Add specifications around the existing code in small compilable increments; if an item cannot yet be verified, keep it executable and explicitly isolate the verification boundary instead of commenting it out.

## Medium

### The verified validity contract omits the documented alignment invariant

- **Guidelines:** `implement-inv-for-models`, `api-preconditions`
- **Location:** `ostd/src/boot/memory_region.rs:40`, `ostd/src/boot/memory_region.rs:69`, `ostd/src/boot/memory_region.rs:93`
- **Evidence:** The public type documentation says, `The region must be page aligned.` Its new invariant is only `self.base + self.len <= MAX_PADDR()`, and `MemoryRegion::new` requires only `base + len <= MAX_PADDR()` before ensuring `res.inv()`.
- **Problem:** The formal notion of a valid `MemoryRegion` admits unaligned bases and ends, contradicting the type's documented validity requirement and allowing `new` to prove `res.inv()` for a region the API documentation calls invalid. Downstream proofs therefore cannot rely on the stated alignment property.
- **Suggestion:** Encode the intended alignment rule in `MemoryRegion::inv()` (for example, require page-aligned `base` and end/length as appropriate to the existing runtime semantics), and give `new` the corresponding precondition. Check the special constructors against the same invariant rather than weakening the documentation.

### `MemoryRegionArrayModel` has unconstrained intrinsic state

- **Guideline:** `implement-inv-for-models`
- **Location:** `specs/ostd/src/memory_region_specs.rs:29`
- **Evidence:** The new model is only `pub ghost struct MemoryRegionArrayModel<const LEN: usize> { pub ghost regions: Seq<MemRegionModel>, pub ghost count: int, }`; unlike `MemRegionModel` above it, it has no `impl Inv` and no other predicate relating `count`, `regions.len()`, or `LEN`.
- **Problem:** Values with negative counts, counts greater than `LEN`, or a count unrelated to the modeled sequence are all admitted. That leaves the model unable to express the central capacity and initialized-prefix invariant of `MemoryRegionArray` and invites every future operation to restate an ad hoc well-formedness condition.
- **Suggestion:** Define `Inv` for `MemoryRegionArrayModel<LEN>` before exposing it, tying `count` to the sequence representation and bounding it by `LEN` (and requiring each modeled region's invariant if the sequence represents active entries). Then make array constructors and mutators establish and preserve that invariant.

## Low

No strong low-severity findings in this fast pass.

## Evidence check record

- Read `diff.patch` in full; treated it as the authoritative change set.
- Inspected the corresponding `after/` source around every reported location and searched the captured tree for live callers of the removed boot and memory-region APIs.
- Checked that no `#[verifier::rlimit(...)]` change appears in the patch; the `rlimit > 200` workflow check is therefore not triggered.
- The patch adds no external specification for a `std`, `core`, or `alloc` API, so the upstream-spec-reuse workflow check is not triggered. No evidence-backed duplicate of the new local models was found in the captured `ostd/specs` and Verus-bearing OSTD context inspected for this fast pass.
- Per the requested fast-review constraints, no repository history was consulted, no subagents were used, no Verus or build verification was run, no exhaustive guideline checklist was performed, and no caller experiment was executed. Findings above are static and have **not** been machine-verified.
