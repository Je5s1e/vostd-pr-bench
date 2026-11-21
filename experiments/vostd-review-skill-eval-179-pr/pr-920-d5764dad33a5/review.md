# Review: PR 920 snapshot `diff.patch`

> Produced from the supplied authoritative patch, its before/after source context, the VOSTD review rubric, and the skill's API-contract criteria.
> Scope: `pr-920-d5764dad33a5/diff.patch`; changed code in `ostd/src/arch/x86/mod.rs` and `verified_libs/vstd_extra/src/external/x86.rs`.

**Bottom line:** The new `has_avx` and `has_avx512` contracts follow from the explicitly documented CPUID trust model, and the inspected patch does not expose a strong maintainability, soundness, invariant, or API-contract defect. The only actionable readiness note is that the new generally reusable specifications for the standard-library CPUID intrinsics should be proposed to upstream Verus. No changed `rlimit` is present.

## High

None.

## Medium

None.

## Low

| Finding | Guideline | Detail |
| --- | --- | --- |
| Propose the standard-library CPUID specifications upstream | `upstream-reusable-specs` | `verified_libs/vstd_extra/src/external/x86.rs:80` and `:90` add `assume_specification` declarations for `core::arch::x86_64::__cpuid` and `core::arch::x86_64::__cpuid_count`. These are standard-library APIs, and their abstract result relation is useful beyond OSTD. The supplied review input contains no upstreaming plan. Propose the specifications and their abstract CPU model to upstream Verus (generalizing the OSTD-specific wording if needed), while retaining the local version until an upstream equivalent is available. |

## Evidence check record

- Read all 149 lines of `diff.patch` and compared both changed files against their supplied `before/` and `after/` versions.
- Checked the new exact-result contracts at `ostd/src/arch/x86/mod.rs:148-175` against `CpuModel::supports_avx`, `CpuModel::supports_avx512f`, `cpuid_consistent`, and the three CPUID external specifications at `verified_libs/vstd_extra/src/external/x86.rs:33-114`. The leaf guards in the implementations match the antecedents in `cpuid_consistent`; no unsupported stronger result was identified.
- Checked the explicit trust assumptions at `verified_libs/vstd_extra/src/external/x86.rs:53-60`: cross-CPU agreement and stability are stated, and the model explicitly does not claim OS enablement or instruction usability. No contradictory caller-visible claim was found in the scoped changes.
- Searched the supplied after-tree for duplicate `CpuModel`, `cpuid_consistent`, and AVX capability specifications; no equivalent existing VOSTD specification was found.
- Inspected the pinned `raw-cpuid` 10.7.0 implementation available in the local Cargo registry. Its `native_cpuid::cpuid_count` delegates directly to `core::arch::__cpuid_count` and copies all four result registers, consistent with the added bridge contract.
- Searched the authoritative patch for `#[verifier::rlimit(...)]`; none was added, removed, or changed, so the `rlimit > 200` workflow check was not triggered.
- The checkout does not contain the full live `docs/coding-guidelines` set referenced by the skill; the review therefore used the bundled skill rubric and the available maintainability guideline snapshot for rule identification. This limitation did not create an additional finding.
- Per the fast-review override, no Verus run, compilation, test, history inspection, caller experiment, or exhaustive rule-by-rule verification was performed. Findings are based on static source evidence only.
