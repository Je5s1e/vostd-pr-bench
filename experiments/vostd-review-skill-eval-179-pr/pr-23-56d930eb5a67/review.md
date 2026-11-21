# Review: PR 23 snapshot 56d930eb5a67

> Produced from the supplied `diff.patch` and its captured `before/` and `after/` context, using the VOSTD maintainability, proof-engineering, API-contract, and limited workflow criteria.
> Scope: `pr-23-56d930eb5a67/diff.patch` (SHA-256 `1f8b641bdca51f5739921625579d5c7eaf7f0a8e626d12ee3b121f2f2872ccf1`).

**Bottom line:** The patch contains one medium-severity proof-reuse issue: it adds a project-local proof that reimplements the same natural-number range theorem introduced in the shared `vstd_extra` layer by this patch. Removing the unused duplicate will keep one canonical proof and avoid later drift. No high-severity issue was found in the supplied snapshot.

## High

None.

## Medium

### Replace the duplicate local range-finiteness proof with the shared lemma

- **Guideline:** `reuse-existing-specifications`
- **Location:** `lock-protocol/src/spec/common.rs:163`
- **Evidence:** The local helper proves
  > `Set::new(|p: nat| pos_in_range(l, r, p)).finite(),`
  > `Set::new(|p: nat| pos_in_range(l, r, p)).len() == (r - l) as nat,`

  and `pos_in_range` is exactly `l <= p < r` (`lock-protocol/src/spec/common.rs:23-25`). The same patch adds the shared `vstd_extra/src/set_extra.rs:13` helper with the equivalent contract
  > `Set::new(|p: nat| l <= p < r).finite(),`
  > `Set::new(|p: nat| l <= p < r).len() == (r - l) as nat,`

  Both functions also duplicate the same `decreases r - l` induction. A static usage search in the captured `after/` tree finds only the local helper's definition and recursive self-call, so it has no current caller.
- **Problem:** This creates two proofs and two public names for the same theorem in the same change, defeating the shared `vstd_extra` abstraction and creating a maintenance point that can drift independently.
- **Suggestion:** Delete `lemma_pos_in_range_set_finite`. If a domain-named bridge is genuinely needed by a caller, keep only a thin wrapper that unfolds `pos_in_range` and calls `vstd_extra::set_extra::lemma_nat_range_finite(l, r)` rather than repeating the induction.

## Low

None.

## Evidence check record

- Read the complete supplied patch and inspected the captured before/after context for every changed path.
- Rechecked the finding against the exact definitions and contracts at `lock-protocol/src/spec/common.rs:23-25,163-179` and `vstd_extra/src/set_extra.rs:13-27`.
- Searched the captured `after/` tree for both lemma names; `lemma_pos_in_range_set_finite` has no caller outside its own recursive body, while `lemma_nat_range_finite` is used by the newly added CPU/NID finiteness proofs.
- The patch adds or changes no `#[verifier::rlimit(...)]`; therefore the `rlimit > 200` workflow check was not triggered.
- Changes from `open`/`closed` declarations to `uninterp` on existing standard-library-facing specs do not change their contracts in the supplied diff, so there was no evidence of a materially changed external specification requiring an upstreaming finding.
- **Verification disclosure:** Per the requested fast-review constraints, no Verus run, build, tests, history inspection, exhaustive rule enumeration, or isolated caller experiment was performed. Conclusions are based only on static inspection of `diff.patch` and the captured before/after files.
