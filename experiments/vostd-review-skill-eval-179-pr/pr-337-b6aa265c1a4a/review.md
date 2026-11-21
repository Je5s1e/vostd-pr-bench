# Review: PR 337 snapshot `b6aa265c1a4a` (fast static review)

## Scope and bottom line

This fast review treats `diff.patch` as authoritative and uses the corresponding `before/` and `after/` files for context. It covers the four changed synchronization files, with attention to maintainability, proof/trust boundaries, assumptions, API contracts, invariants, rlimit changes above 200, and reusable external specifications.

**Bottom line:** do not merge as-is. The newly enabled `RwArc` uses a guardian named and documented as disabling preemption, but the implementation now returns `()` and never disables preemption. That removes a runtime condition needed by a kernel spin lock and can deadlock a CPU. The port also exposes the entire `RwArc` API through trusted bodies without useful contracts and disables its only focused test.

## High

### H1 — `PreemptDisabled` no longer disables preemption, so the enabled `RwArc` can self-deadlock on a preemptible CPU

**Evidence:** `ostd/src/sync/guard.rs:34-53` still documents `PreemptDisabled` as “disabl[ing] preemption while holding a lock”, but changes both associated guard types from `DisabledPreemptGuard` to `()` and changes `guard()` / `read_guard()` from `disable_preempt()` to `()`. The same patch enables `rwarc` in `ostd/src/sync/mod.rs:6,18`, and `ostd/src/sync/rwarc.rs:30-32` selects `RwLock<T, PreemptDisabled>`. `RwLock::try_read`, `try_write`, and `try_upread` retain the guardian in their returned lock guards (`ostd/src/sync/rwlock.rs:389,445,479` and `603-606,678-682`), showing that the guardian lifetime is intended to cover the lock-holding interval.

**Impact:** a task can be preempted while holding this spin-based `RwLock`; if another task scheduled on the same CPU tries to take the conflicting lock, it spins while the holder cannot run. This is a runtime liveness/safety regression, not merely a missing proof annotation. It also contradicts the public type documentation and the `SpinGuardian` invariant that atomic mode is maintained while the lock is held (`guard.rs:4-6`).

**Required correction:** restore `DisabledPreemptGuard` and calls to `disable_preempt()` before exporting `PreemptDisabled` or enabling `RwArc`. If that implementation cannot yet be verified, keep the executable behavior intact behind a narrowly justified trust boundary; do not replace the behavior with a verification-friendly no-op.

## Medium

### M1 — The newly exposed `RwArc` API is almost entirely trusted and has no usable functional contracts

**Evidence:** the patch enables and publicly re-exports `RwArc` / `RoArc` (`ostd/src/sync/mod.rs:6,18`) while adding `#[verifier::external_body]` to `RwArc::new`, `read`, `write`, `get`, `clone_ro`, `Clone::clone`, `Drop::drop`, `get_cloned`, and `RoArc::read` (`ostd/src/sync/rwarc.rs:37-38,47-48,53-54,67-68,84-85,92-93,105-110,116-117,125-126`). None states preconditions or postconditions connecting the result to the input value, the protected allocation, the read/write capability, or the `num_rw` uniqueness condition. The helper used to manufacture the reference in `get` is also trusted (`ostd/src/sync/rwlock.rs:553-563`).

**Impact:** verification accepts the most safety-sensitive bodies—including the unsafe reference construction and reference-count bookkeeping—without checking them, while verified callers receive essentially no semantic API contract. This creates a broad trust island exactly at the ownership/aliasing boundary and prevents callers from establishing even basic facts such as `new(x)` protecting `x`, a read guard observing the same allocation, or `get()` returning that allocation's value when uniqueness holds.

**Required correction:** define a stable abstract model for allocation identity, protected value, and read/write capability; give each public method a contract over that model; then minimize trusted code to the primitive operations that genuinely cannot be verified. In particular, specify and justify the invariant relating `num_rw` to live `RwArc` handles before trusting `get`, `clone`, and `drop` as a group.

### M2 — The only focused `RwArc` regression test is disabled in the same change that enables the module

**Evidence:** `ostd/src/sync/rwarc.rs:132-150` comments out the complete `#[cfg(ktest)]` test module. The removed test exercised the key `num_rw` transition: `get()` succeeds for one `RwArc`, fails after cloning another `RwArc`, and succeeds again after dropping that clone. Meanwhile the patch changes `rwarc` from disabled to compiled and publicly exported in `ostd/src/sync/mod.rs`.

**Impact:** the newly activated ownership/counting path loses its direct regression check, including the acquire/release handoff on which lockless `get()` relies. This makes the broad `external_body` trust boundary in M1 harder to audit and allows runtime behavior to diverge from the intended uniqueness invariant unnoticed.

**Required correction:** keep the focused kernel test active (adapting its placement or annotations for the Verus build if necessary) and add a guardian-behavior test or assertion that demonstrates preemption remains disabled for the full lifetime of guards using `PreemptDisabled`.

## Low

No strong low-severity findings.

## Evidence check record

- Read all 213 lines of `diff.patch` and inspected the complete changed hunks.
- Compared the changed `guard.rs`, `sync/mod.rs`, `rwarc.rs`, and `rwlock.rs` against their `before/` and `after/` snapshots; inspected the surrounding `RwLock` acquisition and guard-storage code to confirm the intended guardian lifetime.
- Checked the patch for `assume`, `admit`, `#[verifier::rlimit]`, and external specification changes. It introduces no new `assume`/`admit`, no rlimit change (and therefore none above 200), and no new or materially changed reusable external specification for `std`, `core`, or `alloc`.
- Attempted to locate this snapshot's coding-guideline pages; they are not included in the PR fixture. Findings therefore rely on the changed source's explicit contracts/documentation and the review's requested proof/trust and API-contract criteria, rather than claiming checklist-level guideline coverage.
- Refutation checks: H1 was checked against all three `G::guard` / `G::read_guard` acquisition sites and the stored guard fields; no alternate preemption-disable path exists in the changed implementation. M1 was checked method-by-method for contracts; none of the listed APIs has `requires`, `ensures`, or `returns`. M2 was checked against the before snapshot, where the test module is active source rather than block-commented.

## Verification disclosure

Per the fast-review override, no Verus run, build, test execution, history analysis, exhaustive checklist pass, or isolated caller experiment was performed. Runtime deadlock impact and proof-interface limitations are based on static source evidence. No finding claims successful compilation or verification.
