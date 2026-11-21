# Review: PR #99 isolated patch

> Scope: `pr-99-08de0794bf8f/diff.patch` is authoritative; the matching `before/` and `after/` snapshots were used only for surrounding context and line locations.

**Bottom line:** The patch makes `PageTableGuard` the concrete guard used by cursor and entry code, but its trusted constructor promises validity for arbitrary raw inputs, and its production PTE update path assumes the key memory-model and preservation facts it advertises. Both defects let downstream proofs consume page-table validity without establishing it, so this patch should not merge until those trust gaps are removed or moved to a narrow, justified boundary.

## High

### `from_raw_paddr` fabricates a well-formed guard from unrestricted inputs

- **Guidelines:** `complete-external-contracts`, `centralize-trusted-boundaries`, `api-preconditions`
- **Location:** `lock-protocol/src/mm/page_table/node/mod.rs:113`
- **Evidence:** `PageTableGuard::wf` requires both `pa_is_valid_pt_address(self.paddr as int)` and `level_is_in_range(self.level as int)` (lines 54–57), where `level_is_in_range` is `1 <= level <= MAX_NR_LEVELS` and a valid page-table address must be a valid kernel address aligned to `SIZEOF_FRAME`. Nevertheless, the new trusted function has no preconditions and states:

  ```rust
  #[verifier::external_body]
  pub fn from_raw_paddr(paddr: Paddr, level: PagingLevel) -> (res: Self)
      ensures
          res.wf(),
          res.paddr_spec() == paddr,
          res.level_spec() == level,
  ```

  Thus calls such as a level of `0` simultaneously yield `res.level_spec() == 0` and `res.wf()`, whose second conjunct says that level is in the range starting at `1`. The old trait constructor only related the returned address to its input; this patch newly strengthens the concrete trusted boundary to assert full validity.
- **Problem:** The contract is false for legal Rust inputs and can inject contradictory facts into every cursor path that reconstructs a guard from a PTE address. `external_body` hides rather than discharges the missing validity obligations.
- **Suggestion:** Require `pa_is_valid_pt_address(paddr as int)` and `level_is_in_range(level as int)` at this boundary, prove those facts at each caller before reconstruction, and remove `external_body` if the struct literal then verifies. If raw reconstruction genuinely depends on a lock/ownership protocol, encode that protocol token in the constructor instead of promising `wf()` from integers alone.

### The concrete PTE mutation path assumes its advertised invariants

- **Guidelines:** `centralize-trusted-boundaries`, `complete-external-contracts`
- **Locations:** `lock-protocol/src/mm/page_table/node/mod.rs:149`; `lock-protocol/src/mm/page_table/node/entry.rs:94`
- **Evidence:** The new concrete `PageTableGuard::write_pte` promises `spt.wf()`, allocator invariants, stable instance IDs, and `frame_keys_do_not_change`, but its body assumes the facts needed to access and preserve the model:

  ```rust
  assume(spt.perms@[frame_idx].1@.mem_contents().is_init());
  ...
  assume(points_to.pptr() == p);
  ...
  assume(idx < frame.ptes.len());
  ...
  assume(spt.wf());  // TODO: P0
  assume(spec_helpers::frame_keys_do_not_change(spt, old(spt)));  // TODO: P0
  ```

  Its caller `Entry::replace` likewise introduces the missing ownership relationship locally:

  ```rust
  assume(spt.perms@.contains_key(exec::frame_addr_to_index_spec(self.node.paddr())));
  // FIXME: Add this to entry well-formedness
  ```

  These assumptions previously lived in the deleted `FakePageTableLock` under `exec/mod.rs`; the patch moves them into the concrete `PageTableGuard` now used by normal cursor and entry APIs.
- **Problem:** Verification of every replacement can now rely on post-state well-formedness and frame preservation even though the implementation explicitly does not prove them. This is a material expansion of the production trust surface, not merely unfinished proof cleanup, and it can conceal a mismatch between `spt.perms`, the pointed-to frame, and `spt.frames`—the body itself calls out that inconsistency as `TODO: P0`.
- **Suggestion:** Make the guard/entry invariant carry the permission-map membership, initialization, pointer identity, and PTE-length facts; require that invariant at the mutation boundary; then prove post-state `spt.wf()` and frame-key preservation from the actual remove/write/reinsert transition. Until that proof exists, keep this implementation out of the verified production guard rather than importing the fake implementation's assumptions.

## Medium

No evidence-backed medium-severity findings.

## Low

No useful low-severity findings.

## Evidence check record

- Read all 808 lines of `diff.patch` and inspected the complete changed `before/` and `after/` files for line-level context.
- Rechecked the new `wf`, `from_raw_paddr`, `write_pte`, and `Entry::replace` contracts and bodies against their direct callers in the captured snapshots. The unrestricted constructor contract directly conflicts with the definition of `wf`; the mutation finding is supported by explicit `assume` statements and the in-source `TODO: P0`/`FIXME` markers.
- No `#[verifier::rlimit(...)]` change appears in the patch, so the `> 200` workflow check did not trigger. No new or materially changed external specification for a `std`, `core`, or `alloc` API appears in scope.
- No separate spec-reuse finding was retained: the changed address/level predicates reuse existing `sub_page_table` helpers rather than introducing competing definitions.
- **Verification disclosure:** Per the fast-review override, no Git history, repository-wide guideline enumeration, Verus run, test, CI run, caller experiment, or exhaustive rule audit was performed. Findings are based solely on static inspection of the authoritative patch and its captured before/after context.
