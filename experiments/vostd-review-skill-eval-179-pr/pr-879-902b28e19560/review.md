# Review: PR 879 supplied patch (fast static review)

> Scope: `diff.patch` is the authoritative change set; `before/` and `after/` were used only for surrounding context and post-change line numbers. This is a fast, non-exhaustive review of maintainability, proof/trust boundaries, assumptions, API contracts, invariants, rlimits above 200, and specification reuse.

**Bottom line:** No strong evidence-backed High, Medium, or useful Low finding was identified in this fast pass. The new logical IRQ protocol consistently couples restoration permissions to the authority identity, CPU, and immediately preceding nesting depth, while the architecture module explicitly documents that hardware/guard integration remains pending and that two runtime bodies are panicking stubs. This result is limited to static inspection and is not a verification result.

## High

No high-severity findings.

## Medium

No medium-severity findings.

## Low

No useful low-severity findings.

## Evidence check record

- Read the complete 363-line `diff.patch` and inspected the affected post-change files plus their immediate before/after context: `ostd/specs/task/irq.rs`, `ostd/specs/task/mod.rs`, `ostd/src/arch/x86/irq.rs`, and `ostd/src/trap/irq.rs`.
- Checked the nested restore protocol statically. `tracked_disable` records the prior view and increments depth (`ostd/specs/task/irq.rs:105-133`); `tracked_restore` requires matching authority identity, CPU, and exactly one preceding depth before consuming the linear permission (`ostd/specs/task/irq.rs:135-157`). The included nested proof restores both state and authority (`ostd/specs/task/irq.rs:160-179`).
- Checked intrinsic validity handling. `LocalIrqState::inv` requires IRQs to be disabled at positive depth (`ostd/specs/task/irq.rs:64-69`); construction, disable, and restore expose preservation clauses, and the restore permission carries the saved-state condition needed when returning to an outer positive depth.
- Checked the changed executable API contract. `DisabledLocalIrqGuard::transfer_to` transfers the saved flag and clears the source (`ostd/src/trap/irq.rs:263-273`), matching the implementation and the inherited `GuardTransfer` no-unwind contract.
- Scanned the patch for `assume`, `admit`, axioms, and rlimit changes. It adds no `assume`, `admit`, axiom, or `#[verifier::rlimit(...)]`, so no rlimit above 200 is present.
- Reviewed all three new `external_body` specifications in `ostd/src/arch/x86/irq.rs:62-85` and `ostd/src/arch/x86/irq.rs:153-180`. Their trust status and implementation limitations are stated directly: `enable_local` leaves STI/NOP unverified, while `disable_local` and `is_local_enabled` explicitly say their pending bodies panic. The latter two do not claim `no_unwind`.
- Searched the supplied post-change verified sources for an existing local-IRQ nesting model or equivalent restoration permission. No overlapping model was found. The patch does not add or materially change an external specification for a `std`, `core`, or `alloc` API, so the upstream-spec workflow check is not triggered.
- No history inspection, Verus run, compilation, CI run, standalone proof, or caller experiment was performed, per the requested fast review mode. Consequently, this report makes no claim that the patch parses, compiles, or verifies.
