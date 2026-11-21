# Review: `diff.patch` (isolated PR 916 snapshot)

> Produced from the supplied patch, its `before/` and `after/` trees, and the VOSTD coding-guideline criteria available in the workspace.
> Scope: fast, non-exhaustive isolated review of `pr-916-d7cdf470b297/diff.patch`; surrounding source was read from the paired snapshots.

**Bottom line:** The verified PE-header API exposes a precondition that other modules cannot unfold, so a verified caller cannot establish the contract through the advertised predicate. The patch also adds generally reusable trusted specifications for two `core` integer methods locally instead of proposing them to Verus/vstd. No high-severity issue was established by this limited static review.

## High

None.

## Medium

### Make the exported precondition caller-provable

- **Guideline:** `keep-internal-spec-helpers-closed`
- **Location:** `ostd/libs/linux-bzimage/builder/src/pe_header.rs:671`
- **Evidence:** `make_pe_coff_header` is `pub(crate)` and requires `valid_setup_elf(setup_elf)` at lines 281–288, while its predicate is declared `pub(crate) closed spec fn valid_setup_elf` at line 671. Its body is the only definition of the parsing, segment, and arithmetic obligations (lines 672–679).
- **Problem:** A verified caller outside this module can name `valid_setup_elf`, but cannot unfold a `closed` predicate to prove it. This is precisely the guideline's exception to keeping implementation helpers closed: a predicate used as a caller obligation must be open or accompanied by an exported introduction lemma.
- **Suggestion:** Make `valid_setup_elf` `pub(crate) open spec fn`, or keep it closed and export a suitable lemma/API that lets crate callers establish the predicate without exposing unwanted representation details.

## Low

| Finding | Guideline | Detail |
|---|---|---|
| Propose the new integer specs upstream | `upstream-reusable-specs` | `verified_libs/vstd_extra/src/external/int_specs.rs:12` and `:19` add trusted specs for the general-purpose `core` APIs `u16::to_le_bytes` and `u32::to_le_bytes`. The after-tree contains no other specifications for these methods. Propose these reusable contracts to Verus/vstd (and link the proposal here); retain a local compatibility copy only while the pinned upstream lacks them. |

## Evidence check record

- Read all 1,261 lines of `diff.patch`, then inspected the complete changed implementations in the `after/` snapshot and relevant call sites in both snapshots.
- Confirmed that the sole current runtime call to `make_pe_coff_header` is in `builder/src/lib.rs:65`; that caller is not itself brought under verification by this patch. This does not refute the contract-usability issue for the newly exported crate-level verified API.
- Searched the after-tree for specifications of `u16::to_le_bytes` and `u32::to_le_bytes`; only the two newly added local `assume_specification` declarations were found.
- Searched the patch for `#[verifier::rlimit(...)]`; none was added or changed, so the numeric rlimit check was not triggered.
- The newly added `bytemuck` and `xmas-elf` contracts target third-party crates, so the upstreamable-`std`/`core`/`alloc` workflow check applies only to the two integer specifications above.
- The authoritative guideline pages were not included in this isolated snapshot. The review used the requested skill and the available workspace copy of the maintainability rules; findings were limited to rules whose wording and code evidence were directly available.
- **No-verification disclosure:** Per the requested fast-review constraints, I did not run Verus, compile the crate, inspect repository history, execute caller experiments, delegate persona passes, or perform the exhaustive skill checklist. Conclusions are static and non-exhaustive.
