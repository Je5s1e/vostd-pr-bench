# Review: PR #770 (`diff.patch` with supplied before/after context)

> Scope: the 1,610-line `diff.patch` in this review bundle is authoritative; the matching files under `before/` and `after/` were used only for line-numbered context. The bundle contains no branch or commit SHA metadata.
>
> Verification disclosure: fast static review only. Per the requested override, I did not run Verus, Rust builds, tests, caller experiments, history analysis, or exhaustive guideline checks.

**Bottom line:** This change should not merge as-is. It removes a substantial part of the executable CPU subsystem to make the verification slice fit, and its new trusted `num_cpus` contract treats a boot-mutated global as one immutable logical value. The public `CpuSet` contracts also do not expose two central documented results.

## High

### H1 — The verification change comments out production CPU APIs and initialization

**Guideline:** `preserve-exec-code`  
**Location:** `ostd/src/cpu/mod.rs:5`, `ostd/src/cpu/mod.rs:10`, `ostd/src/cpu/mod.rs:35`, `ostd/src/cpu/mod.rs:145`; `ostd/src/cpu/set.rs:874`

**Evidence:** The after-image contains `// pub mod local;`, `// pub use crate::arch::cpu::*;`, comments out `CpuId::current_racy`, and wraps lines 145–230—`CURRENT_CPU`, `PinCurrentCpu`, `init_on_bsp`, and `init_on_ap`—in one block comment. The before-image has all of these as executable items at `ostd/src/cpu/mod.rs:3`, `:8`, `:29-41`, and `:100-185`. It also replaces the public conversion implementation with `/* impl From<CpuId> for CpuSet { ... } */` (after `ostd/src/cpu/set.rs:874-880`; before `:142-148`).

This is an API and boot-behavior deletion, not a proof-only change. Among other effects, the BSP path no longer discovers the processor count or calls `init_num_cpus`, so `NUM_CPUS` remains its initializer value of one in the remaining code.

**Suggestion:** Restore the executable module exports, current-CPU state, boot/AP initialization, `PinCurrentCpu`, and `From<CpuId>` implementation. Verify them incrementally or leave the still-unverified items executable with an explicitly scoped trust boundary; do not comment them out to reduce the verification target.

### H2 — `num_cpus` is trusted to equal a fixed spec value even though its global changes at boot

**Guideline:** `complete-external-contracts`  
**Location:** `ostd/src/cpu/mod.rs:67`, `ostd/src/cpu/mod.rs:77`, `ostd/src/cpu/mod.rs:95`, `ostd/src/cpu/mod.rs:121`

**Evidence:** The executable state starts as `static mut NUM_CPUS: u32 = 1` and `init_num_cpus` executes `NUM_CPUS = num_cpus` (`:67`, `:77-82`). Nevertheless, the new external-body contract says `returns cpu_count() as usize` (`:95-103`), while `cpu_count()` is one uninterpreted spec constant and its documentation calls the value a “stable constant” (`:121-125`). The before-image shows the intended boot call `init_num_cpus(num_cpus)` at `ostd/src/cpu/mod.rs:173`.

A safe call before initialization returns `1`; a safe call after initialization can return a larger machine CPU count. Both cannot equal the same immutable `cpu_count()` value. Trusting this contract can therefore prove facts about runtime CPU-set sizes that are false during one of those phases. H1 currently masks the transition by deleting the initialization path, but restoring required boot behavior immediately exposes the contradiction.

**Suggestion:** Model the initialization phase/state explicitly and tie the stable abstract count to a post-initialization invariant. Require that invariant/token on verified callers of `num_cpus`, or verify boot initialization before publishing an immutable count. Do not give the unrestricted safe getter a time-independent exact result while the underlying global is still mutable.

## Medium

### M1 — Public query/iterator contracts omit their documented result semantics

**Guideline:** `api-postconditions`  
**Location:** `ostd/src/cpu/set.rs:625`, `ostd/src/cpu/set.rs:716`

**Evidence:** `is_full` is documented as “Returns true if the set is full,” but its contract only provides `ret ==> self@ == Set::range(0, cpu_count())` (`:625-631`). Thus a verified caller cannot conclude that a non-full set makes the result false. `iter` promises iteration over the set in ascending order (`:716-718`), but its contract only states prophetic-iterator laws and the presence of a decrease metric (`:719-725`); it never relates yielded `CpuId`s to `self@`, proves completeness/no duplicates, or exposes ascending order.

These are the primary observable meanings of the two APIs, so the contracts are not sufficient for their natural verified callers.

**Suggestion:** Make `is_full` exact, e.g. `returns self@ == Set::range(0, cpu_count())`. Give `iter` an abstract remaining-sequence contract that is the strictly ascending enumeration of `self@` (or an equivalent reusable set-to-sorted-sequence predicate), and connect `IteratorSpec::remaining(&ret)` to it.

## Low

No low-severity findings. The fast pass intentionally omits cosmetic and completeness-only documentation nits.

## Evidence check record

- Read the authoritative patch in full and compared the cited regions with the supplied before/after files.
- Confirmed the executable deletions directly in before/after context: CPU-local exports/state/initialization, current-CPU APIs, and `From<CpuId>` are executable before and commented out after.
- Confirmed the trust mismatch statically: `NUM_CPUS` is initialized to `1`, is assigned by `init_num_cpus`, and the unrestricted external-body getter returns one immutable `cpu_count()` spec value.
- Confirmed no added or changed `#[verifier::rlimit(...)]` appears in `diff.patch`; there is no `rlimit > 200` finding.
- The patch adds external specifications for `core` APIs (`u64::count_ones`, `usize::div_ceil`, and slice `fill`) and for `smallvec`. Their upstreamability and exact dependency-source conformance were not checked under the fast-review override.
- No verification, build, test, history, or isolated caller experiment was performed; conclusions above are based solely on quoted static evidence.
