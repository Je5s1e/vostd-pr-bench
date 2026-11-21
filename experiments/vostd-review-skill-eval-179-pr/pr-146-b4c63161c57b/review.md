# Review: PR #146 (`481c455c8d890c55fd8c9fe4f6460acbb23e4b6d..6747158e33ae6c85efbe0f7485cb3e614d9a9e51`)

> Fast, non-exhaustive review of the supplied `diff.patch`, using the supplied before/after snapshots for context.
> Scope: `pr https://github.com/asterinas/vostd/pull/146 main=481c455c8d890c55fd8c9fe4f6460acbb23e4b6d head=6747158e33ae6c85efbe0f7485cb3e614d9a9e51`.

**Bottom line:** The revised `alloc_if_none` contract now admits the intended empty-entry state, but the implementation declares exactly that state unreachable with `assume(false)` and uses the contradiction to promise `Some`. This is a blocking contract/proof mismatch. The same path also introduces two further trusted assumptions and a local axiom for facts that should be proved or exported by the responsible abstraction.

## High

### `alloc_if_none` proves its advertised success result from a contradiction

- **Guidelines:** `api-postconditions`, `centralize-trusted-boundaries`
- **Location:** `lock-protocol/src/mm/page_table/node/entry.rs:397`
- **Evidence:** The new preconditions require both logical entry maps to be absent:

  ```rust
  !old(spt).i_ptes.value().contains_key(old(self).pte.pte_paddr() as int),
  !old(spt).ptes.value().contains_key(old(self).pte.pte_paddr() as int),
  ```

  and the postcondition promises `res is Some` (`entry.rs:407`). Yet the implementation handles a non-present PTE as follows (`entry.rs:429-432`):

  ```rust
  if !self.pte.is_present() {
      assume(false);
      // The entry is already present.
      return None;
  }
  ```

  `Entry::is_none` states that absence from both maps corresponds to `!self.pte.is_present()` (`entry.rs:84-97`). Thus the newly admitted, intended input reaches the branch that returns `None`; verification obtains the unconditional `Some` guarantee only by assuming a contradiction. The comment also says the opposite of the condition.
- **Suggestion:** Remove the contradiction and align the branch with the API. Under the current absent-entry preconditions, prove the PTE is non-present (for example through the existing `is_none` abstraction) and proceed with allocation; if a fallible contract is intended instead, change the condition/contract so a genuinely present entry returns `None` and specify both outcomes without an `assume`.

## Medium

### Allocation freshness is dropped at the wrapper and reintroduced as a caller-local assumption

- **Guidelines:** `complete-external-contracts`, `centralize-trusted-boundaries`
- **Location:** `lock-protocol/src/mm/page_table/node/mod.rs:105`
- **Evidence:** `exec::alloc_page_table` still ensures

  ```rust
  !old(model).meta_map.contains_key(res.0.start_paddr() as int),
  ```

  at `lock-protocol/src/exec/mod.rs:74`, but `PageTableNode::alloc` comments out the corresponding postcondition at `node/mod.rs:105`. Its caller then adds a new trust step (`entry.rs:437-438`):

  ```rust
  // TODO: where should we enforce this?
  assume(!spt.frames.value().contains_key(pt.start_paddr() as int));
  ```

  `SubPageTable::wf` already relates every frame address to an allocator metadata entry (`spec/sub_pt/mod.rs:60-67`), so allocator freshness is the abstraction-level fact from which frame freshness should be derived. Dropping it from the wrapper forces a valid allocation property to become an unchecked caller fact.
- **Suggestion:** Restore the freshness postcondition on `PageTableNode::alloc`, forwarding the existing guarantee from `exec::alloc_page_table`, and prove frame-map freshness from `old(spt).wf()` plus that guarantee. Remove the local `assume`.

### The state-machine update is bridged to the next verified operation by assuming the whole invariant

- **Guideline:** `centralize-trusted-boundaries`
- **Location:** `lock-protocol/src/mm/page_table/node/entry.rs:484`
- **Evidence:** Immediately after `set_child` and inserting the new permission, the patch adds:

  ```rust
  assume(spt.wf());  // TODO
  self.node.write_pte(..., Tracked(spt));
  ```

  `write_pte` requires `old(spt).wf()` (`node/mod.rs:210-217`) and then exports `spt.wf()`. Assuming the entire invariant at this handoff allows every subsequent assertion and the public postconditions of `alloc_if_none` to rely on an unchecked global state relation, rather than on the transition and permission update just performed.
- **Suggestion:** Prove each conjunct of `spt.wf()` from the `set_child` transition, allocator/frame freshness, and the permission insertion before calling `write_pte`. If the transition API does not export a needed preservation fact, strengthen that abstraction at its definition rather than admitting the full caller state.

### A derivable numeric conversion is introduced as a project-local axiom

- **Guidelines:** `centralize-trusted-boundaries`, `reuse-existing-specifications`
- **Location:** `lock-protocol/src/helpers/conversion.rs:5`
- **Evidence:** The new helper is declared trusted:

  ```rust
  pub axiom fn usize_mod_is_int_mod(x: usize, m: usize, z: usize)
      requires x % m == z,
      ensures (x as int) % (m as int) == (z as int),
  ;
  ```

  It is used only to establish the alignment conjunct of `IntermediatePageTableEntryView::wf` at `entry.rs:453-458`. This is an arithmetic cast/modulo bridge, not an external runtime behavior that requires a trusted model, so making it an axiom unnecessarily enlarges the soundness boundary.
- **Suggestion:** Replace it with a proved lemma (including the divisor condition required by the actual modulo definitions), or use the corresponding checked vstd integer/cast lemma if available. Keep any unavoidable trusted numeric bridge in the shared external-spec boundary rather than a general local `helpers` module.

## Low

No strong low-severity findings.

## Evidence check record

- Read the supplied patch in full and compared all changed files against the supplied before/after snapshots.
- Re-read `Entry::wf`, `Entry::is_none`, `alloc_if_none`, `SubPageTable::wf`, `PageTableNode::alloc`, `exec::alloc_page_table`, and `write_pte` to challenge the premises above.
- Confirmed that the lower allocation boundary retains allocator-map freshness while the wrapper removes it, and that `SubPageTable::wf` links frame membership to allocator metadata membership.
- Confirmed that no `#[verifier::rlimit(...)]` was added or changed and no `std`/`core`/`alloc` external specification was introduced, so the two narrow workflow checks do not trigger.
- No claim is made that `usize_mod_is_int_mod` is logically false; the issue is that a routine arithmetic bridge is admitted rather than proved.
- Per the requested fast mode, no Verus run, CI run, history analysis, caller experiment, exhaustive guideline checklist, or persona delegation was performed. The repository snapshot does not contain its own `docs/coding-guidelines` pages; rule names and criteria were taken from the supplied VOSTD review skill, with the available guideline material used only as supporting context.
