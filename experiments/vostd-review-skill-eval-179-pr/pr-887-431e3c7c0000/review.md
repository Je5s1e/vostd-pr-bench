# Review: PR 887 snapshot `431e3c7c0000`

> Produced from `diff.patch`, the captured `before/` and `after/` trees, and the VOSTD review skill's maintainability, proof-engineering, and API-contract criteria.
> Scope: fast, non-exhaustive static review of the changes represented by `diff.patch`; no history inspection, caller experiment, Verus run, or CI verification was performed.

**Bottom line:** The patch cannot merge in its current form because it makes verification progress by removing core x86 execution paths from the compiled crate: CPU-local storage, exception construction, context execution, FPU handling, trap initialization/dispatch, and the public `UserMode` implementation are all wrapped in comments. This is a direct violation of `preserve-exec-code` and materially changes the runtime/API surface. Separately, the new trusted `wrfsbase` boundary is left inside the verified implementation instead of being isolated as an external specification.

## High

### H1 — Verification comments out production x86 functionality

- **Guideline:** `preserve-exec-code`
- **Locations:** `ostd/src/arch/x86/cpu/mod.rs:4`, `ostd/src/arch/x86/cpu/context/mod.rs:170`, `ostd/src/arch/x86/cpu/context/mod.rs:361`, `ostd/src/arch/x86/cpu/context/mod.rs:669`, `ostd/src/arch/x86/trap/mod.rs:26`, `ostd/src/arch/x86/trap/mod.rs:117`, `ostd/src/arch/x86/trap/mod.rs:156`, `ostd/src/user.rs:5`, `ostd/src/user.rs:96`
- **Evidence:** The after-tree contains `/* GS storage awaits ... Origin Rust: pub mod local; */`; wraps `CpuException::new` in a block comment; wraps `impl UserContextApiInternal for UserContext` (including execution and trap-frame construction) in a block comment; wraps the FPU implementation in a block comment; wraps the trap submodules, `init`, and all trap dispatch in block comments; and wraps `UserContextApiInternal`, `UserMode`, and `ReturnReason` in block comments. In the before-tree these are live compiled items, for example `pub mod local;` at `ostd/src/arch/x86/cpu/mod.rs:4`, `pub(crate) fn new(...)` at `ostd/src/arch/x86/cpu/context/mod.rs:148`, trap modules at `ostd/src/arch/x86/trap/mod.rs:17-19`, and `pub struct UserMode` at `ostd/src/user.rs:61`.
- **Problem:** This is not a proof-only change. It deletes the kernel's CPU-local, exception, user-mode execution, FPU, trap initialization, and trap-handling paths from compilation and removes public user-mode APIs. The module comments acknowledge the missing contracts, but missing verification support does not justify changing executable behavior or the exported API.
- **Suggestion:** Restore the executable code and module declarations exactly in place. Restrict `#[verus_verify]` to the subset that can currently be verified, and isolate unsupported dependencies with the narrowest permitted external specifications or verification boundaries without commenting out their callers or runtime implementations. If some code truly must be changed for Verus, keep the change minimal and demonstrate runtime equivalence to the original.

## Medium

### M1 — `activate_tls_pointer` introduces a local trusted body instead of an external model

- **Guideline:** `centralize-trusted-boundaries`
- **Location:** `ostd/src/arch/x86/cpu/context/mod.rs:354`
- **Evidence:** The new method annotation is `#[verus_verify(external_body)]` followed by an empty `#[verus_spec]`, while its body directly executes `unsafe { wrfsbase(self.fsbase() as u64) }`.
- **Problem:** The verified implementation now carries an opaque trusted body locally. Although the rustdoc admits that no hardware-state postcondition is modeled, leaving the trust marker on the caller-facing wrapper obscures the exact external operation being trusted and makes future callers depend on a boundary that cannot be reused or audited independently.
- **Suggestion:** Put the `wrfsbase` trust boundary in the repository's external-specification layer with the original signature and the narrowest truthful contract, then keep `activate_tls_pointer` as ordinary executable code verified against that specification. If no meaningful hardware-state model exists yet, explicitly model only the absence of a usable postcondition rather than marking the whole wrapper external.

## Low

No low-severity findings.

## Evidence check record

- Read all 736 lines of `diff.patch` and inspected the cited `before/` and `after/` source around each changed region.
- Confirmed that the removed functionality is live executable code in `before/` and block-commented in `after/`; H1 does not rely on a build failure inference.
- Searched the changed after-tree for `external_body`, `uninterp`, `axiom`, `assume`, `admit`, and `#[verifier::rlimit]`. The CPU-count uninterpreted function and bounds axiom are moved from `ostd/src/cpu/mod.rs` to `ostd/specs/cpu.rs` without a material semantic change. No changed `rlimit` above 200 was found.
- Reviewed the new `UserContextApi` trait contracts and concrete implementation statically; no strong precondition or postcondition defect was established in this fast pass.
- No claim was made that the patch fails Verus or CI. Per the requested fast-review constraints, no Verus verification, compilation, history analysis, exhaustive guideline checklist, caller experiment, or external source lookup was performed; conclusions are limited to the quoted static evidence.
