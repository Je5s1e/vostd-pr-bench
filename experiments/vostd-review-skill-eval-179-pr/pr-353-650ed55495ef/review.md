# Review: PR #353 captured patch (fast isolated review)

> Produced from the supplied `diff.patch`, with the supplied `before/` and `after/` trees used for context. This was a fast, non-exhaustive static review; no history inspection, Verus run, build, tests, or caller experiments were performed.
> Scope: `pr-353-650ed55495ef/diff.patch` (11 changed files; captured head label `650ed55495ef`).

**Bottom line:** This patch is not merge-ready. It brings wait queues and IRQ guards back into the compiled API while replacing the interrupt, scheduler, task-identity, context-switch, and guard-cleanup behavior on which they depend with panics, no-ops, dummy values, or comments. It also introduces an unchecked representation cast for mutable lock access and marks nearly every newly enabled wait/guard body trusted, so neither the runtime behavior nor the relevant proof boundary is preserved.

## High

### H1 — Re-enabled wait/IRQ APIs depend on removed runtime behavior

- **Guideline:** `preserve-exec-code`
- **Locations:** `ostd/src/arch/x86/irq.rs:86`, `ostd/src/sync/wait.rs:192`, `ostd/src/task/scheduler/mod.rs:86`, `ostd/src/task/scheduler/mod.rs:547`, `ostd/src/trap/irq.rs:256`
- **Quoted evidence:** `arch/x86/irq.rs` changes both `disable_local` and `is_local_enabled` from real x86 operations to `unimplemented!()` (lines 86–93). `Waiter::new_pair` replaces `Task::current().unwrap().cloned()` with `Arc::new(Task {})` (wait.rs:192–197), while `Waker::wake_up` still passes that task to `scheduler::unpark_target` (lines 282–289). `inject_scheduler` now has an empty body because `SCHEDULER.call_once(...)` and timer registration are block-commented (scheduler/mod.rs:86–97), and `reschedule` computes `next_task` but comments out `processor::switch_to_task(next_task)` (lines 547–580). Finally, the `Drop` implementation that re-enabled IRQs when `was_enabled` is true is block-commented (trap/irq.rs:256–262), although `disable_local` still documents automatic restoration on drop (lines 198–202).
- **Problem:** These are observable semantic deletions, not proof-only changes. Constructing an IRQ guard immediately panics; if those stubs were filled, dropping the guard would still no longer restore interrupts. The wait path associates its waker with a fabricated empty task, scheduler injection cannot initialize `SCHEDULER`, and a reschedule decision never performs a context switch. The newly exported `WaitQueue`, `Waiter`, and `Waker` therefore cannot satisfy their existing runtime documentation.
- **Suggestion:** Restore the original executable IRQ, task identity, scheduler initialization/context-switch, and guard `Drop` implementations verbatim before adding verification annotations. Isolate any not-yet-verifiable body at the verification boundary without changing what runs, and enable one dependency-complete slice at a time.

### H2 — `DerefMut` fabricates an `UnsafeCell<T>` view of a `PCell<T>`

- **Guidelines:** `preserve-exec-code`, `centralize-trusted-boundaries`
- **Location:** `ostd/src/sync/spin.rs:448`
- **Quoted evidence:** The new implementation performs `let ucell: *const UnsafeCell<T> = (&self.lock.inner.val as *const PCell<T>).cast();` followed by `&mut *(*ucell).get()` (lines 448–454). The adjacent verified immutable `Deref` instead obtains a tracked permission and calls `self.lock.inner.val.borrow(Tracked(read_perm))` (lines 432–443). No layout equivalence between `PCell<T>` and `UnsafeCell<T>` or mutable permission is established in the patch.
- **Problem:** A raw-pointer cast does not establish that two unrelated wrapper types have the same representation, and it bypasses `PCell`'s permission discipline to create a mutable reference. This changes a lock guard's core unsafe access path without a stated or checked representation/synchronization argument, so it can invalidate both Rust aliasing safety and the verified ownership model.
- **Suggestion:** Implement mutable access through `PCell`'s supported mutable-borrow API using the guard's tracked write permission, analogous to the immutable `borrow` path. If an unavoidable external bridge is required, put the smallest bridge in the repository's explicit external boundary and state the exact layout, exclusivity, and lifetime conditions; do not reinterpret the field inline.

## Medium

### M1 — The enabled wait/guard surface is accepted through local trusted bodies

- **Guidelines:** `centralize-trusted-boundaries`, `complete-external-contracts`
- **Locations:** `ostd/src/sync/wait.rs:54`, `ostd/src/sync/wait.rs:191`, `ostd/src/sync/wait.rs:261`, `ostd/src/sync/guard.rs:102`
- **Quoted evidence:** The patch adds 23 `#[verifier::external_body]` occurrences: the external type wrapper plus guard methods, and essentially every constructor, wait, wake, enqueue, access, drop, and helper body newly enabled in `sync/wait.rs`. For example, `WaitQueue::wait_until` (wait.rs:73–90), `Waiter::new_pair` (191–202), `Waiter::drop` (260–269), and `Waker::wake_up` (282–290) are all trusted. None of these APIs gains a `requires`/`ensures` contract in the patch.
- **Problem:** Verification does not check the newly activated concurrency and lifecycle logic, and verified callers receive no useful state-transition or wake-delivery facts from it. Keeping these trusted annotations beside ordinary callers also obscures which minimal OS/atomic behaviors are actually intended to be trusted, especially while the bodies contain the runtime substitutions in H1.
- **Suggestion:** Restore correct executable behavior first, specify the minimal caller-visible queue/waker and guard properties, and verify the ordinary coordination logic. Centralize only irreducible architecture/atomic models in the established external-specification layer with complete contracts; remove local `external_body` annotations from deterministic wrappers and protocol code.

## Low

No evidence-backed low-severity findings in this fast pass.

## Evidence check record

- Read all 639 lines of `diff.patch` and compared the cited hunks against the supplied before/after files. The primary violating locations above are added or materially changed by the patch.
- Refutation check for H1: the after-snapshot still calls the affected paths (`DisabledLocalIrqGuard::new` calls both IRQ stubs; `Waker::wake_up` calls `unpark_target`; `park_current` reaches `reschedule`). The removed cleanup and context-switch code is present only inside comments, so it cannot restore runtime behavior.
- Refutation check for H2: the patch supplies no `repr(transparent)`, layout lemma, external specification, or tracked mutable permission connecting `PCell<T>` to `UnsafeCell<T>`. The checked neighboring immutable implementation demonstrates that `PCell` access is permission-bearing.
- Trust scan: 23 added `external_body` occurrences; no added `assume`, `admit`, axiom, `requires`, `ensures`, or `#[verifier::rlimit(...)]` was found. Thus there is no changed rlimit above 200. No new or materially changed external specification for a `std`, `core`, or `alloc` API was found, and no duplicate reusable spec was introduced in scope.
- **No-verification disclosure:** Per the requested fast-review constraints, this review did not inspect Git history, run Verus, compile the crate, execute tests, perform exhaustive guideline coverage, or run isolated caller/spec experiments. Findings are based on direct static before/after evidence only.
