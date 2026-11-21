# Review: `diff.patch` (PR 870 snapshot)

> Fast, non-exhaustive review against the VOSTD maintainability, proof-engineering, API-contract, and narrowly scoped workflow criteria.
> Scope: the immutable 153-line `diff.patch`, covering `ostd/src/arch/x86/mod.rs` and `ostd/src/arch/x86/task/mod.rs`, with the supplied `before/` and `after/` trees used only for surrounding context.

**Bottom line:** The added contracts are direct models of the affected field updates, and the diff introduces no assumptions, admits, external specifications, or `#[verifier::rlimit]` changes. One maintainability issue should be fixed before merge: the verification patch unnecessarily rewrites the executable bodies of both constructors instead of preserving the original Rust.

## High

None.

## Medium

### Preserve the executable constructor bodies

- **Guideline:** `preserve-exec-code`
- **Location:** `ostd/src/arch/x86/task/mod.rs:44` and `ostd/src/arch/x86/task/mod.rs:90`
- **Quoted evidence:** Before, `TaskContext::new` used `Self {` followed by separate `regs:`, `rip:`, and `fsbase:` lines; after, line 45 is `Self { regs: CalleeRegs::new(), rip: 0, fsbase: 0 }`. Before, `CalleeRegs::new` likewise placed `rsp` through `r15` on separate lines; after, line 91 is `CalleeRegs { rsp: 0, rbx: 0, rbp: 0, r12: 0, r13: 0, r14: 0, r15: 0 }`. The diff gives no Verus-required reason and retains no adjacent `Origin Rust:` record.
- **Problem:** VOSTD's `preserve-exec-code` rule requires verification changes to leave executable Rust intact unless Verus forces a minimal rewrite. These formatting rewrites add review noise and make it harder to distinguish proof-only changes from runtime changes.
- **Suggestion:** Restore both constructor bodies byte-for-byte to their original multiline forms and leave only the surrounding verification attributes and contracts as additions.

## Low

None.

## Evidence check record

- Read all 153 lines of `diff.patch` and compared each changed file with its supplied `before/` and `after/` versions.
- Checked the new `TaskContextView` and every added contract against the executable field assignments. The setters preserve all fields not named in their struct update, the getters return the represented fields, and on the x86-64 target the `usize`/`u64` stack-pointer conversions do not introduce a contract mismatch.
- Inspected the surrounding `TaskContextApi` declaration and representative callers. No strong evidence showed that the added implementation contracts overstate accepted inputs or returned state.
- Searched the scoped diff for `assume`, `admit`, trusted/external bodies, external `std`/`core`/`alloc` specifications, and `#[verifier::rlimit]`; none were introduced. Consequently, there is no rlimit-over-200 or upstream-spec-reuse finding.
- Searched the supplied tree for uses of the new model. `TaskContextView` is used by the constructor and accessor contracts, so it is not an unused speculative helper.
- Per the requested fast-review scope, I did not inspect Git history, run Verus or CI, execute isolated caller experiments, or perform the exhaustive persona/checklist workflow. Findings are therefore based on static source evidence only.
