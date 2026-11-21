# Review: PR #237 e5b76915..24bb220c (fast isolated review)

> Produced from the repository's VOSTD review criteria in fast, non-exhaustive mode.
> Scope: authoritative `diff.patch`, comparison `e5b76915e9af647deffc1704d2de2285c4c35a88..24bb220c78790484164f0f5c6f6adb19f15a3669`; before/after snapshots were used only for context.

**Bottom line:** The change exports two new broadcast arithmetic lemmas with `admit()` as their complete proofs. These are independent trust holes for align-up and align-down, and the same patch strengthens the corresponding executable API contracts to equate their results with those models. Both proof roots should be completed before merge.

## High

### The align-up model is exported through an admitted theorem

- **Guideline:** `centralize-trusted-boundaries`
- **Location:** `vstd_extra/src/arithmetic.rs:23` (trust hole at line 33); related strengthened contract at `ostd/libs/align_ext/src/lib.rs:63`
- **Evidence:** The patch adds `pub broadcast proof fn lemma_nat_align_up_sound(...)` with the caller-visible guarantees `nat_align_up(x, align) >= x`, divisibility, and leastness, but its entire body is `admit();`. It also adds `ret == nat_align_up(self as nat, align as nat)` to `AlignExt::align_up`.
- **Problem:** This publishes the align-up arithmetic facts as trusted rather than checked facts. Because the new equality postcondition connects the executable result to this model, the PR's main align-up contract extension lacks a completed proof chain.
- **Suggestion:** Prove `lemma_nat_align_up_sound` from division/modulo lemmas and replace the existing `align_up` method's proof admission with a checked bit-mask/modulo bridge that establishes the new equality postcondition. Keep the two facts out of the broadcast group until their proofs verify.

### The align-down model is exported through a separate admitted theorem

- **Guideline:** `centralize-trusted-boundaries`
- **Location:** `vstd_extra/src/arithmetic.rs:36` (trust hole at line 46); related strengthened contract at `ostd/libs/align_ext/src/lib.rs:80`
- **Evidence:** The patch adds `pub broadcast proof fn lemma_nat_align_down_sound(...)` with the caller-visible guarantees `nat_align_down(x, align) <= x`, divisibility, and greatestness, but its entire body is `admit();`. It also adds `ret == nat_align_down(self as nat, align as nat)` to `AlignExt::align_down`.
- **Problem:** This independently trusts the align-down extremal theorem and exposes it through `group_arithmetic_lemmas`. The align-down executable contract extension therefore also lacks a completed proof chain.
- **Suggestion:** Prove `lemma_nat_align_down_sound` from the quotient/remainder characterization and replace the existing `align_down` method's proof admission with a checked proof that the bit-mask implementation equals `nat_align_down`. Do not broadcast the theorem while its body remains admitted.

## Medium

No medium-severity findings.

## Low

No low-severity findings.

## Evidence check record

- Read all 134 lines of the authoritative `diff.patch` (SHA-256 `f635423427c63a3509ddc7e670521624afc8fc2a2965442ec8bc8839107bf57a`) and inspected the relevant before/after files with source line numbers.
- Confirmed that the method-level `proof! { admit(); }` blocks predate this patch; the in-scope change strengthens both method contracts, while the two admitted public broadcast lemmas are newly introduced by this patch.
- Confirmed the two theorem bodies are exactly `admit();` and both lemmas are added to `group_arithmetic_lemmas`.
- Searched the supplied after snapshot's active verified-code roots for equivalent `nat_align_up`/`nat_align_down` specifications; no duplicate implementation was found outside the newly added module.
- No added or changed `#[verifier::rlimit(...)]` occurs in the authoritative patch, so the `rlimit > 200` workflow check was not triggered. No new or materially changed external specification for a `std`, `core`, or `alloc` API was present.
- No Verus run, build, tests, caller experiment, history analysis, or exhaustive guideline pass was performed, as required by this fast isolated review. Findings are based on static patch and snapshot evidence only.
