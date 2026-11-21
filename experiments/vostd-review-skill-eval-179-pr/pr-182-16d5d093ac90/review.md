# Review: `diff.patch` (`fe9835da9d23028bd6f70181ed99d9eca466f147..16d5d093ac90ba94baa5f82bb07f95b32657e29a`)

> Fast, non-exhaustive VOSTD review of the authoritative `diff.patch`, using the captured `before/` and `after/` files as context.
> Scope: three changed files under `lock-protocol/src/spec/`; static review only.

**Bottom line:** The patch repairs the missing distinctness precondition on `lemma_brothers_have_different_offset`, but moves its trusted proof into a new, more general public lemma. Because that reconstruction lemma is implemented solely with `admit()`, every verified caller may assume its equality without a proof. This trust-boundary expansion should block merge until the lemma is proved or moved to an explicitly reviewed trust boundary.

## High

### The new public reconstruction lemma is admitted

- **Guideline:** `centralize-trusted-boundaries`
- **Location:** `lock-protocol/src/spec/utils.rs:1666`
- **Evidence:**

  ```rust
  pub proof fn lemma_get_parent_get_offset_sound(nid: NodeId)
      requires
          Self::valid_nid(nid),
          nid != Self::root_id(),
      ensures
          Self::get_child(Self::get_parent(nid), Self::get_offset(nid)) == nid,
  {
      broadcast use {
          NodeHelper::lemma_get_parent_sound,
          NodeHelper::lemma_get_offset_sound,
          NodeHelper::lemma_get_child_sound,
      };

      admit();
  }
  ```

  The patch then invokes this admitted result twice at lines 1693–1694 to prove `lemma_brothers_have_different_offset`. Compared with the captured base, the `admit()` is no longer confined to that specific two-node result: it now backs a public one-node round-trip theorem that any proof can call. Although adding `nid1 != nid2` to the downstream lemma correctly fixes its former contract, the new generalized fact remains an unchecked trust boundary inside an ordinary specification module.

  **Suggestion:** prove `lemma_get_parent_get_offset_sound` from the existing parent, offset, child, trace, and algebraic lemmas, removing `admit()`. If the fact genuinely cannot be proved with the current model, keep it out of this ordinary proof module and place the minimal assumption in the project’s explicit external/trusted boundary with its rationale and applicability documented.

## Medium

No findings.

## Low

No findings.

## Evidence check record

- Read all 613 lines of the authoritative `diff.patch` and inspected the complete captured before/after versions of all three changed files.
- Confirmed that the base had an `admit()` in `lemma_brothers_have_different_offset`, while the patch adds the necessary `nid1 != nid2` precondition, removes that local `admit()`, introduces `lemma_get_parent_get_offset_sound`, and calls the new admitted lemma twice from the repaired proof.
- Checked the definitions and nearby contracts for `get_parent`, `get_offset`, `get_child`, and their soundness lemmas. No static evidence refuted the reconstruction property; the finding concerns its unproved, public trust status and broader reuse surface, not a claim that the equality is false.
- No added or changed `#[verifier::rlimit(...)]` was present, so the `rlimit > 200` workflow check did not trigger. No new or materially changed `std`, `core`, or `alloc` external specification was present.
- The changed API preconditions and postconditions were inspected statically. In particular, the new `nid1 != nid2` requirement is necessary for the promised unequal offsets; no separate contract finding survived review.
- The repository snapshot does not contain `docs/coding-guidelines/`; the review therefore used the rule identifiers and requirements embedded in the supplied VOSTD review skill, and records this as a coverage limitation.
- Per the requested fast mode, no Git history, Verus execution, exhaustive rule enumeration, caller experiment, or other dynamic verification was performed. CI or Verus success was not independently verified.
