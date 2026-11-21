# Review: PR #424 patch snapshot 8d7b6621ed81

> Scope: `pr-424-8d7b6621ed81/diff.patch`, with the supplied `before/` and `after/` context. Fast static VOSTD review of changed code only.

**Bottom line:** This patch should not merge while verified page-table and virtual-memory paths still depend on two new `admit()` calls and an unchecked overflow `assume()`. It also substantially expands the trusted surface through local axioms/external bodies and adds five `rlimit` values above the VOSTD cap. These are proof-integrity issues, not cosmetic cleanup.

## High

### Verified mapping and unmapping paths still contain explicit proof holes

- **Guidelines:** `preserve-exec-code`, `centralize-trusted-boundaries`
- **Locations:** `ostd/src/mm/kspace/kvirt_area.rs:639`, `ostd/src/mm/page_table/cursor/mod.rs:2394`, `ostd/src/mm/vm_space.rs:861`
- **Quoted evidence:**

  ```rust
  assert(forall |i: int| (it.pos as int + 1) <= i < it.elements.len() ==>
      CursorMut::<'a, KernelPtConfig, A>::item_slot_in_regions(...))
  by { admit() }

  assert(owner.inv()) by { admit() };

  //*** KNOWN BUG: `self.virt_addr() + len` could overflow. For now, assume that it doesn't. ***
  assume(self.pt_cursor.0.va + len <= usize::MAX);
  ```

  The first `admit()` supplies preservation of the remaining frame-slot obligations after `cursor.map`; the second supplies the cursor invariant immediately before `push_level`. The `assume()` suppresses a stated overflow bug on `CursorMut::unmap`, and the same unchecked addition is then used to compute `end_va`. Consequently, successful verification does not establish these paths from their declared preconditions.

  **Suggestion:** Prove the per-frame preservation fact by carrying uniqueness/remaining-slot facts in the loop invariant; prove `owner.inv()` from the reconstructed continuation and child-owner relations before reinsertion; and replace the overflow assumption with a caller-visible precondition or a checked executable bound that matches the intended API behavior. Do not count these functions as verified until all three gaps are discharged or explicitly authorized and isolated as reviewed trust boundaries.

## Medium

### The patch distributes new trusted facts through implementation and model modules

- **Guideline:** `centralize-trusted-boundaries`
- **Representative locations:** `ostd/specs/mm/frame/meta_owners.rs:101-119`, `ostd/specs/mm/page_table/cursor/owners.rs:131-166`, `ostd/specs/mm/page_table/node/entry_owners.rs:106-146`, `ostd/src/mm/kspace/mod.rs:388-409`, `ostd/src/mm/page_table/mod.rs:740-773`, `ostd/src/mm/vm_space.rs:1617`
- **Quoted evidence:**

  ```rust
  pub uninterp spec fn is_mmio_paddr(pa: Paddr) -> bool;
  pub broadcast axiom fn axiom_mmio_usage_iff_mmio_paddr(slot: MetaSlotOwner) ...;
  pub axiom fn axiom_mmio_paddr_huge_page_closed(...) ...;

  pub axiom fn make_cont(...) -> (res: Self) ...
  pub axiom fn restore(...) -> (tracked guard: PageTableGuard<'rcu, C>) ...
  pub axiom fn new(...) -> (res: Self) ...

  pub axiom fn axiom_top_level_index_range_bounds<C: PageTableConfig>() ...
  pub axiom fn axiom_leading_bits_only_when_high_half<C: PageTableConfig>() ...
  ```

  These facts are load-bearing for MMIO/allocator disjointness, cursor construction, and address-range reasoning, but they are declared beside their consumers across `ostd/specs` and `ostd/src`. That makes the trusted base difficult to audit and allows application proofs to rely on unchecked structural and hardware-layout claims without a single reviewed boundary.

  **Suggestion:** Move genuinely environmental or executable-model assumptions into a narrow external-spec boundary (with architecture/configuration validity predicates where needed), replace derivable facts with proof lemmas, and make callers import that boundary rather than declaring axioms locally. In particular, prove constructor postconditions from tracked operations wherever possible and restrict the MMIO closure claim to the reviewed architectures/ranges that guarantee it.

### Five newly added or raised solver limits exceed the project cap

- **Guideline:** `decompose-before-raising-rlimit`
- **Locations:** `ostd/specs/mm/page_table/cursor/owners.rs:1208` (`2000`), `ostd/specs/mm/page_table/cursor/owners.rs:1389` (`20000`, raised from `10000`), `ostd/specs/mm/page_table/mod.rs:443` (`400`), `ostd/src/mm/page_table/cursor/mod.rs:730` (`800`, raised from `400`), `ostd/src/mm/page_table/cursor/mod.rs:3277` (`10000`)
- **Quoted evidence:**

  ```rust
  #[verifier::rlimit(2000)]
  #[verifier::rlimit(20000)]
  #[verifier::rlimit(400)]
  #[verifier::rlimit(800)]
  #[verifier::rlimit(10000)]
  ```

  Each value is above the workflow rule's maximum of 200, including two increases to already excessive limits.

  **Suggestion:** Refactor or split the affected proofs until each verifies at `rlimit <= 200`; keep the existing `60` and `200` additions unchanged.

## Low

No strong low-severity findings.

## Evidence check record

- Read the complete immutable `diff.patch` scope and inspected the surrounding unified-diff hunks for every reported location.
- Compared the supplied `before/` and `after/` files; this snapshot contains only unchanged `COPYRIGHT` and `LICENSE-MPL` context outside the patch, so no additional source snapshots were available.
- Enumerated added `admit()`, `assume()`, `external_body`, `uninterp spec fn`, `axiom fn`, and `#[verifier::rlimit(...)]` occurrences directly from the patch. The reported rlimit set excludes the compliant additions at 60 and 200.
- No claim here depends on PR history, CI output, or a caller experiment.
- **No-verification disclosure:** Per the fast-review instruction, no Verus run, build, test, isolated caller experiment, history inspection, or exhaustive guideline pass was performed. Findings are based on static patch evidence; verification status was not independently checked.
