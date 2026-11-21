# Review: `diff.patch` (`before` → `after`)

> Produced from the supplied VOSTD review criteria and the skill's API-contract criteria.
> Scope: the authoritative `pr-17-30beab687be4/diff.patch`, with `before/` and `after/` used only as surrounding context.

**Bottom line:** The new safety verification still trusts an unproved loop fact via an active `assume`, so the relevant recycling proof is not fully checked. In addition, `process_remote_requests` documents and executes remote TLB processing but its public contract exposes neither that the requests were issued nor that the current CPU was removed from their target sets, which prevents a caller from using it to establish the flush-before-reclaim argument. A large second implementation/model is also present in the patch but excluded from compilation and verification by commented-out module declarations.

## High

### The recycling proof admits its key preservation step

- **Guideline:** `centralize-trusted-boundaries`
- **Location:** `fvt13-vmspace-unmap-safety/src/tlb/cpu_local_queue/mod.rs:114`
- **Evidence:** The active loop body contains:

  ```rust
  // Actually the assumption is proved here.
  // It can be proved by Verus automatically before the vector 'push'.
  assume(forall|i: int|
      #![auto]
      pages@.len() < i < pages_ghost.len() ==> {
          !all_cpu_sets[pages_ghost.len() - i - 1].is_empty_spec()
              ==> new_pages@.contains(pages_ghost[i])
      });
  ```

  This is not an external/environmental fact: it is an ordinary loop-preservation obligation over local vectors. The comment itself says it is provable, but `assume` makes the verifier trust it and therefore leaves the recycling argument dependent on an unchecked proposition.
- **Suggestion:** Prove the quantified preservation fact immediately before mutating `new_pages` (or restructure the invariant/index relation so Verus retains it across `push`) and remove the `assume`. Do not move this local fact into a trusted boundary.

### The remote-processing contract does not establish that any flush occurred

- **Guideline:** `api-postconditions`
- **Location:** `fvt13-vmspace-unmap-safety/src/tlb/cpu_local_queue/mod.rs:211`
- **Evidence:** The function is documented as “Check the remote CPU's requests and process them,” calls `op.perform_on_current(...)` and removes the CPU at lines 242–250, but its entire postcondition is:

  ```rust
  ensures
      self.invariants(),
  ```

  It finally returns `Tracked(tlb)` at line 267, while the updated `__tlb` is used only for an internal assertion. The internal quantified assertion at lines 262–265 is likewise absent from `ensures`.
- **Problem:** A caller receives no fact that the returned TLB model issued the queued operations and no fact that `current` was persistently removed from each applicable `target_cpus`. Those are precisely the facts needed before `recycle` may treat an empty target set as permission to release deferred pages; successful verification of this body therefore does not provide a usable cross-call safety contract.
- **Suggestion:** Return the updated tracked TLB model and strengthen `ensures` with an abstract postcondition stating that every request targeting `current` was issued and that the corresponding persistent removal token/fact holds. Express this through a stable model predicate rather than exposing the vector representation.

## Medium

### Newly added proof models are excluded from the verification target

- **Guideline:** `avoid-unused-spec-helpers`
- **Location:** `fvt13-vmspace-unmap-safety/src/tlb/mod.rs:2`
- **Evidence:** The module root contains:

  ```rust
  mod cpu_local_queue;
  // pub mod local_queue;
  // pub mod model;
  ```

  and the active queue module similarly begins with `// mod model;`. Consequently, the newly added `tlb/local_queue.rs`, `tlb/model.rs`, and `tlb/cpu_local_queue/model.rs` are not part of the crate even though they contain hundreds of lines of spec/proof APIs (including `OpsStackModel`, `KeptPageVecModel`, and their lemmas).
- **Problem:** Cargo/Verus can report success without parsing or verifying this substantial portion of the patch. These helpers have no active consumers and the checked crate does not cover the apparent end-to-end TLB/page-reclamation model.
- **Suggestion:** Either wire the intended modules into `tlb/mod.rs` and resolve their verification obligations in this change, or remove the excluded files and introduce their models only together with the active proof that consumes them.

## Low

No low-severity findings.

## Evidence check record

- Treated `pr-17-30beab687be4/diff.patch` (2,068 lines) as the immutable authoritative change and used the matching `after/` files for numbered source context.
- Confirmed statically that the `assume` is in the active `cpu_local_queue` module and is not inside commented-out code.
- Confirmed statically that `process_remote_requests` performs/removes internally but exposes only `self.invariants()` and returns the original `tlb` binding.
- Confirmed statically that `tlb/local_queue.rs`, `tlb/model.rs`, and `tlb/cpu_local_queue/model.rs` are disconnected by commented-out module declarations.
- No `#[verifier::rlimit(...)]` change appears in the patch, so the `rlimit > 200` workflow check did not trigger. No new or materially changed external specification for a `std`, `core`, or `alloc` API appears in active code.
- **Verification disclosure:** Per the fast-review constraint, no Verus run, caller experiment, repository history analysis, or exhaustive guideline checklist was performed. Findings are based on static patch and before/after-context evidence only.
