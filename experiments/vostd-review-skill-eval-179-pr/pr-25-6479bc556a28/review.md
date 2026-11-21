# Review: PR 25 snapshot `diff.patch`

> Produced from the VOSTD coding-guideline criteria and the supplied immutable before/after snapshots.
> Scope: `pr-25-6479bc556a28/diff.patch`, changing `lock-protocol/src/spec/utils.rs`; no branch or commit SHA metadata was supplied.

**Bottom line:** This patch does not finish removing the trust hole from `lemma_in_subtree_bounded_is_child`. It moves the original top-level `admit()` into a nested proof of the crucial parent relationship and then derives the public lemma's postcondition from that admitted fact. This should block merge until the nested admission is replaced by a checked proof.

## High

### The public subtree-bound lemma still depends on an admitted parent fact

- **Guideline:** `centralize-trusted-boundaries` / `reuse-existing-specifications`
- **Location:** `lock-protocol/src/spec/utils.rs:960`
- **Evidence:** The changed proof contains:

  ```rust
  assert(pa == Self::get_parent(ch)) by {
      // is_child implies parent-child relationship
      Self::is_child(pa, ch);
      // FIXME: need to prove this without admit
      admit();
  }
  ```

  The admitted equality is immediately used to establish the trace-prefix relationship at lines 987-999, which feeds the calculation of `ch` and ultimately the public postcondition `next_outside_subtree(ch) <= next_outside_subtree(pa)` declared at lines 673-679. The pre-existing `lemma_parent_child` at lines 1248-1282 proves only `is_child(get_parent(nid), nid)`; it does not provide the reverse/uniqueness fact needed here.
- **Problem:** Replacing the lemma body's original `admit()` with a longer proof that contains another `admit()` does not make this exported fact fully verified. The later comments saying that the equivalence and positional formula have been proved obscure that the key parent/trace bridge remains trusted.
- **Suggestion:** Prove a reusable child-parent uniqueness/trace-prefix lemma from `is_child(pa, ch)` and the existing trace conversion lemmas, then invoke it here and remove the nested `admit()`. If that reverse direction is not derivable from the present definitions, strengthen the model or contract explicitly instead of trusting the equality locally.

## Medium

None.

## Low

None.

## Evidence check record

- Read all 537 lines of `diff.patch` and compared the affected lemma in the supplied `before` and `after` snapshots.
- Inspected the definitions and contracts of `is_child`, `get_parent`, `lemma_nid_to_trace`, `lemma_trace_to_nid_increment`, and `lemma_parent_child` in the after snapshot. The available `lemma_parent_child` establishes the opposite direction and does not refute the finding.
- Searched the patch for trust constructs and rlimit changes. The changed hunk removes one top-level `admit()` and adds one nested `admit()`; it adds no `assume`, `external_body`, `#[verifier::rlimit(...)]`, or standard-library external specification.
- The patch changes only a proof body, so it introduces no API precondition/postcondition change or executable invariant change to assess separately.
- **No-verification disclosure:** Per the fast-review override, no Git history inspection, Verus run, caller experiment, exhaustive guideline checklist, or sub-agent pass was performed. The finding is based on direct static evidence and does not claim whether the remaining non-admitted proof steps verify.
