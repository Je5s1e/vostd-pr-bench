# Review: PR 692 snapshot (`diff.patch`)

> Produced from the VOSTD coding-guideline checks requested for this fast review and the skill's API-contract criteria.
> Scope: the authoritative `diff.patch`, with `before/` and `after/` used only as surrounding context; no repository history was consulted.

**Bottom line:** The patch exposes the timer module for verification by commenting out the timer's executable implementation, including x86 interrupt initialization, elapsed-time updates, and callback registration. That violates `preserve-exec-code` and leaves the newly exposed timer API without its original runtime behavior, so this should block the change. The new generally useful model of `core::time::Duration::new` should also be proposed to upstream Verus rather than becoming a VOSTD-only trust boundary.

## High

### The verification port removes the executable timer implementation

- **Guideline:** `preserve-exec-code`
- **Location:** `ostd/src/arch/x86/timer/mod.rs:7` (also `ostd/src/timer/mod.rs:5`)
- **Evidence:** The new block comment beginning at x86 timer line 7 removes `mod apic`, `mod hpet`, and `pit`, while the block beginning at line 38 removes `init_bsp`, `init_ap`, and `timer_callback`. In the before-image, `timer_callback` contains `crate::timer::jiffies::ELAPSED.fetch_add(1, Ordering::SeqCst);` and invokes every registered callback; in the after-image those statements are inside the comment. Likewise, `ostd/src/timer/mod.rs:5-28` comments out `INTERRUPT_CALLBACKS` and the public `register_callback` implementation, while `ostd/src/lib.rs:53` newly enables `pub mod timer;`.
- **Problem:** This is not a proof-only refactoring: it removes the hardware timer setup and the only x86 path in this scope that advances `ELAPSED`, and it deletes the callback API's implementation. Consequently `Jiffies::elapsed()` can no longer reflect x86 timer ticks through the original mechanism, and users cannot register timer callbacks through the original implementation.
- **Suggestion:** Restore the original executable timer modules, initialization, interrupt handler, elapsed counter update, and callback registry byte-for-byte. Add Verus annotations/specifications around that code incrementally; if the current verification frontier cannot yet admit a dependency, keep the timer module outside that frontier rather than deleting its executable behavior with block comments.

## Medium

No medium-severity findings.

## Low

| Finding | Guideline | Detail |
|---|---|---|
| Propose the `Duration::new` external specification upstream | `upstream-reusable-specs` | `verified_libs/vstd_extra/src/external/time.rs:6-15` adds a project-local model and `assume_specification` for the standard-library API `core::time::Duration::new`. The signature, normalization/overflow precondition, return model, and `no_unwind` behavior are generally useful to any Verus client, while the patch records no upstreaming plan. Propose this model to upstream Verus (and track that proposal) so the ecosystem has one maintained trust boundary; keep a local copy only as a documented temporary bridge if necessary. |

## Evidence check record

- Read all 245 lines of `diff.patch`; treated it as the immutable, authoritative change.
- Compared the affected `before/` and `after/` timer sources with numbered lines. This confirmed that the block comments encompass the executable x86 timer initialization, interrupt callback, `ELAPSED.fetch_add`, and callback registry, rather than merely enclosing imports or specifications.
- Searched the after-image for `ELAPSED`, `register_callback`, `init_bsp`, and `init_ap`. The x86 update and initialization occurrences remain only textually inside the newly added comments; the riscv update is irrelevant because this snapshot selects x86 via `ostd/src/lib.rs:35-36`.
- Checked `diff.patch` for `#[verifier::rlimit(...)]`; none is added or changed, so the `rlimit > 200` workflow check is not triggered.
- Checked the new external specification's stated panic boundary: its precondition `secs + (nanos / 1_000_000_000) as u64 <= u64::MAX` excludes the carry overflow under which `Duration::new` can panic, and its `no_unwind` claim is conditional on that precondition. No separate contract-correctness finding is supported by the static evidence reviewed.
- **No-verification disclosure:** Per the fast-review override, no Verus run, build, isolated caller experiment, history inspection, or exhaustive guideline enumeration was performed. Findings are based solely on static inspection of `diff.patch` and its supplied before/after context.
