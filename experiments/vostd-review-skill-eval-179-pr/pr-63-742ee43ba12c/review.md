# Review: isolated `diff.patch` (before → after)

> Produced from the VOSTD maintainability/proof-engineering criteria and the skill's API-contract criteria.
> Scope: fast, non-exhaustive static review of `diff.patch`, with `before/` and `after/` used only for surrounding context.

**Bottom line:** The explicit flag conversion is substantially easier to audit than the removed generic mapping tables, but its verification now depends on three newly admitted `ilog2` fact bundles. Those facts are simple constant arithmetic and should be proved rather than added to the trusted base, especially because they are load-bearing for the verified executable encoders and decoders. No high-severity API-contract defect was established by this limited static pass.

## High

None.

## Medium

### M1 — Constant bit-position facts are admitted into the trusted base

- **Guideline:** minimize-trusted-code / explicit-assumptions
- **Locations:** `lock-protocol/src/exec/rw/pte/page_prop.rs:335`, `lock-protocol/src/exec/rw/pte/page_prop.rs:462`, `lock-protocol/src/exec/rw/pte/page_table_flags.rs:181`
- **Quoted evidence:** Each newly added `lemma_consts_properties` is annotated `#[verifier::external_body]` and has an empty body, while promising facts such as `Self::NO_EXECUTE().bits().ilog2() == 63`. `format_flags` and `format_property` call these lemmas at `page_table_entry.rs:135-137` and `page_table_entry.rs:197-199` before using `parse_flags!`, whose shifts are computed from `.ilog2()` (`page_table_entry.rs:36-40`).
- **Problem:** The patch removes `external_body` from the two executable translation functions, but replaces part of their proof with three trusted lemmas. Because those postconditions determine the shift distances used to relate the executable result to its specification, a mistake in any admitted constant can make verification accept an incorrect flag translation. These are finite, concrete arithmetic claims, and `page_table_flags.rs` already imports `lemma2_to64`, `lemma2_to64_rest`, `pow2`, `log`, and `lemma_log_pow` without using them, which is strong local evidence that a checked proof was feasible and intended.
- **Suggestion:** Give all three lemmas verified bodies using the imported power/logarithm lemmas (or direct bit-vector assertions where supported), and remove `#[verifier::external_body]`. If Verus cannot currently prove a specific case, isolate only that case behind a narrowly documented axiom rather than admitting the entire bundle.

## Low

None.

## Evidence check record

- Read all 1,307 lines of `diff.patch` and inspected the corresponding `before/` and `after/` files for the five changed paths.
- Searched the after-tree for `rlimit`, `external_body`, `axiom`, `assume`, and `admit`. The patch adds no `#[verifier::rlimit(...)]`; therefore the workflow rlimit cap is not triggered. The changes to `vstd_extra/src/array_ptr.rs` make three existing trust boundaries explicit `axiom fn`s rather than introducing stronger contracts.
- Checked the load-bearing use sites of the three new external lemmas and the definition of `parse_flags!`; the admitted `ilog2` results directly select the shifts in both encoding and decoding.
- Checked the exact-result API edits (`ensures res == ...` → `returns ...`) and found them consistent with the result types and the VOSTD `use-returns-for-exact-results` rule in the inspected scope.
- No Verus run, build, history inspection, caller experiment, or exhaustive guideline pass was performed, as required by this fast isolated review. Consequently, this report does not claim compilation or verification success.
