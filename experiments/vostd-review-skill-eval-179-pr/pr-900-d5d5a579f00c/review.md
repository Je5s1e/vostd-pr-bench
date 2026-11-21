# Review: PR #900 snapshot `d5d5a579f00c`

> Produced from the VOSTD coding-guideline review criteria and the skill's API-contract criteria.
> Scope: the authoritative `diff.patch`, with `before/` and `after/` used only for surrounding context and source line numbers.

**Bottom line:** The new `Drop` implementation makes local-IRQ restoration operational, but its correctness depends on guards being destroyed in LIFO order even though the safe API does not enforce that order. A safe caller can therefore leave one `DisabledLocalIrqGuard` alive while an earlier guard re-enables interrupts, invalidating the guard and lock atomicity invariants. This should be fixed before merge with restoration state that is robust to safe out-of-order destruction, or with an API that structurally enforces nesting.

## High

### A live IRQ guard does not guarantee that IRQs remain disabled

- **Guideline:** `api-preconditions`
- **Location:** `ostd/src/trap/irq.rs:277`
- **Evidence:** The changed documentation says, “`Nested guards must be dropped in reverse order`” (`ostd/src/trap/irq.rs:202-203`), while the newly enabled destructor executes `if self.was_enabled { irq::enable_local(); }` (`ostd/src/trap/irq.rs:277-281`). Construction records the current flag independently for each guard (`let was_enabled = irq::is_local_enabled(); ... Self { was_enabled }`, lines 251-257). Thus safe code can create `outer` while IRQs are enabled, create `inner` while they are disabled, and then call `drop(outer)` before `drop(inner)`; dropping `outer` enables IRQs while `inner` remains live. `DisabledPreemptGuard` now embeds this same guard (`ostd/src/task/preempt/guard.rs:108-110`), and `PreemptDisabled` lock guardians obtain it through `disable_preempt()` (`ostd/src/task/preempt/guard.rs:136-141`).
- **Problem:** LIFO destruction is a correctness precondition for the new runtime behavior, but it is neither expressed nor enforced by the safe API. This can break the advertised disabled-IRQ/preemption state while protected code or a spin-lock guard is still active, allowing interrupt re-entry into a region whose atomicity depends on that state.
- **Suggestion:** Make restoration robust to arbitrary safe drop order, for example by maintaining per-CPU IRQ-guard depth plus the state to restore when the depth reaches zero. Alternatively, redesign acquisition so the type/lifetime structure enforces properly nested destruction; documentation alone is insufficient for a safety-critical invariant exposed through safe `drop`.

## Medium

No medium-severity findings.

## Low

No low-severity findings.

## Evidence check record

- Read all 470 lines of `diff.patch`; inspected the corresponding before/after context for `cpu_core.rs`, `arch/x86/irq.rs`, `task/preempt/guard.rs`, `trap/irq.rs`, and the affected `SpinGuardian` definitions and call sites.
- Confirmed statically that the LIFO condition is documented but not encoded in ownership or lifetimes, and that `Drop` can re-enable IRQs solely from an individual guard's captured `was_enabled` bit.
- No `#[verifier::rlimit(...)]` change is present, and no new or materially changed external specification for a `std`, `core`, or `alloc` API is present.
- Per the requested fast review override, no history inspection, Verus run, build, test, exhaustive-rule enumeration, or isolated caller experiment was performed. The finding is based on direct control-flow and safe-Rust destruction semantics; verification status was not independently checked.
