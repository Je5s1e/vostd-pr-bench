# Review: PR 546 isolated `diff.patch`

> Produced from the VOSTD review skill's maintainability, proof-engineering, API-contract, and targeted workflow criteria.
> Scope: fast, non-exhaustive static review of `diff.patch` against the supplied `before/` and `after/` trees (30 files; 6,221 insertions and 596 deletions).

**Bottom line:** The patch should not merge with `axiom_fresh_loose_id_not_in_dom` as written: its unrestricted public contract is false for a map whose domain is all integers, so it makes the trusted logic inconsistent. The new linked-list embedding also records the wrong abstract position for `push_back`, and the patch adds seventeen public axioms beside their consumers instead of keeping the new trusted surface centralized and auditable.

## High

### An unrestricted fresh-key axiom is inconsistent

- **Guideline:** `complete-external-contracts`
- **Location:** `ostd/specs/mm/embedding/list_store.rs:351`
- **Quoted evidence:**

  ```rust
  pub open spec fn fresh_loose_id<...>(m: Map<LooseId, ...>) -> LooseId {
      choose|id: LooseId| !m.dom().contains(id)
  }

  pub axiom fn axiom_fresh_loose_id_not_in_dom<...>(m: Map<LooseId, ...>)
      ensures
          !m.dom().contains(fresh_loose_id(m)),
  ;
  ```

  The adjacent list-key version at lines 249-260 requires both domains to be finite, and `ListStore::inv` establishes `self.loose.dom().finite()` at line 119. The loose-key axiom has no corresponding precondition.
- **Problem:** `Map` is not intrinsically finite. For a legal map whose domain contains every `int`, there is no witness satisfying the `choose` predicate, but the public axiom still ensures that its result is outside the domain. Instantiating it with such a map proves `false`, invalidating every verification result in the crate rather than merely over-approximating the embedding.
- **Suggestion:** Replace the axiom with a proved lemma requiring `m.dom().finite()` (the file already has that fact at every current call site), using the same finite-integer-set argument as `lemma_fresh_segment_id_not_in_dom` and `lemma_fresh_unique_id_not_in_dom`. If it must remain trusted temporarily, add the finite-domain precondition and move the trust declaration to the centralized boundary described below.

## Medium

### The trusted `push_back` model inserts before the last element

- **Guideline:** `complete-external-contracts`
- **Location:** `ostd/specs/mm/embedding/list_store.rs:436`
- **Quoted evidence:**

  ```rust
  /// ... the frame is spliced in at the *tail* ...
  old(owner).list.len() > 0 ==> final(owner).list == old(owner).list.insert(
      old(owner).list.len() as int - 1,
      final(frame_own).meta_own,
  ),
  ```

  The executable API documents “The new frame is inserted at the back” (`ostd/src/mm/frame/linked_list.rs:256`), and the existing behavioral test states that pushing `3` onto `2 1` yields `2 1 3` (`ostd/src/mm/frame/test.rs:108-123`). Inserting at `len - 1` instead yields `2 3 1` for that model sequence.
- **Problem:** The newly added axiom is presented as a trusted reflection of the executable operation, but its ordered-sequence postcondition contradicts both the documented tail behavior and the concrete test. `ListStore::step_push_back` can therefore establish the wrong list order, so later one-step proofs do not model the runtime API they claim to cover. The same `len - 1` clause already appears in the executable API contract; copying it into a new axiom compounds rather than isolates the defect.
- **Suggestion:** Specify nonempty `push_back` as insertion at `old(owner).list.len()` (or an equivalent append), correct the executable contract and the embedding together, and prove the wrapper from the corrected `insert_before`/cursor contract rather than trusting a duplicated postcondition.

### Seventeen new public axioms are distributed beside their consumers

- **Guideline:** `centralize-trusted-boundaries`
- **Locations:** `ostd/specs/mm/embedding/kvirt_store.rs:109`; `ostd/specs/mm/embedding/list_store.rs:232-715`; `ostd/specs/mm/embedding/segment.rs:368`; `ostd/specs/mm/embedding/unique.rs:74-197`; `ostd/specs/mm/embedding/mod.rs:5402`
- **Quoted evidence:** The patch adds seventeen declarations matching `+pub axiom fn`, including `query_embedded`, ten list-store constructors/operation reflections, `segment_clone_embedded`, four unique-frame lifecycle reflections, and `axiom_unique_entry_new`. Representative text says:

  ```rust
  pub axiom fn query_embedded<'rcu>(...)
  pub axiom fn push_front_embedded<...>(...)
  pub axiom fn segment_clone_embedded(...)
  pub axiom fn unique_from_unused_embedded(...)
  ```

- **Problem:** These declarations grant caller-visible trusted facts inside ordinary embedding modules, immediately beside proofs that consume them. That makes the trust base difficult to inventory and permits internal clients to bypass the verified executable contracts; the inconsistent fresh-key axiom above demonstrates the practical risk. Comments calling an axiom a “trusted reflection” do not establish equivalence to the executable operation.
- **Suggestion:** Eliminate axioms that are mathematical lemmas or tracked-data constructors by proving them. For unavoidable executable reflections, expose one narrow centralized boundary (for example under `vstd_extra::external` or a dedicated embedding trust module), preserve the original API signatures and complete contracts, and have local step proofs call verified wrappers. Keep the boundary private where cross-module use is unnecessary.

## Low

None.

## Evidence check record

- Read the complete isolated patch and the supplied `before/`/`after/` context for the reported locations. The authoritative guideline pages named by the skill are not present in this isolated workspace, so rule IDs were checked against the skill's bundled persona definitions.
- Counted exactly 17 newly added `pub axiom fn` declarations from added patch lines. Existing axioms outside changed lines were used only as context.
- Refuted the fresh-key contract statically with the legal total-domain-map case and compared it with the finite-domain premises already present in `ListStore::inv` and the neighboring proved fresh-ID lemmas.
- Checked the `push_back` sequence clause against its new axiom documentation, the executable API documentation, and the existing `2 1` then `push_back(3)` behavioral test.
- No added, removed, or changed `#[verifier::rlimit(...)]` was found, so the `rlimit > 200` workflow check was not triggered. No new or materially changed external specification for a `std`, `core`, or `alloc` API was found.
- **Verification disclosure:** Per the requested fast mode, no Verus/Z3 run, caller experiment, history inspection, CI run, or exhaustive rule-by-rule audit was performed. Findings are based on static contract and before/after evidence only.
