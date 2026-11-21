# Review: PR 3 snapshot (`diff.patch`)

> Scope: `pr-3-df3e68c119ce/diff.patch`, treated as authoritative and checked against the supplied `before/` and `after/` files. The snapshot does not provide branch or commit metadata.

**Bottom line:** The new explicit triggers expose an admitted trace theorem whose postcondition contradicts the adjacent empty-path theorem; that inconsistency can make the proof context contradictory and should block merging. The patch also turns two previously checked bodies into trusted external bodies without isolating or explaining either trust boundary. No `rlimit` above 200 or changed standard-library external specification appears in the patch.

## High

### The triggered trace-length theorem is inconsistent for an empty path

- **Guideline:** `complete-external-contracts`
- **Location:** `vstd_extra/src/ghost_tree.rs:1421`, `vstd_extra/src/ghost_tree.rs:1440`
- **Evidence:** The patch adds explicit triggers to both `#[trigger]self.trace(path) == seq![self.root.value]` under `path.len() == 0` and the unconditional admitted claim `#[trigger]self.trace(path).len() <= path.len()`. For an empty path, the first statement gives a trace of length 1, while the second gives a trace length at most 0.
- **Problem:** The two exported broadcast facts are contradictory for the same legal argument. Adding explicit triggers makes this inconsistent admitted contract an especially dangerous source of automatic instantiations, allowing downstream proofs to derive arbitrary facts once both statements are in scope.
- **Suggestion:** Correct the length contract to the property implemented by `trace` (apparently `self.trace(path).len() <= path.len() + 1`), prove it without `admit()`, and add a trigger only to that verified theorem. Add an empty-path proof case so the off-by-one boundary is checked directly.

## Medium

### A complete recursive-visit proof is replaced by a local axiom

- **Guideline:** `centralize-trusted-boundaries`
- **Location:** `vstd_extra/src/ghost_tree.rs:969`
- **Evidence:** The patch adds `#[verifier::external_body]` to `lemma_recursive_visit_induction`, while retaining its full proof body at lines 982–1024.
- **Problem:** Verus no longer checks the retained assertions as a proof of the postcondition; callers instead trust the theorem. This expands the trusted base in a general-purpose proof library and leaves a body that misleadingly looks verified.
- **Suggestion:** Remove `#[verifier::external_body]` and repair the proof obligation. If a temporary assumption is genuinely unavoidable, isolate the smallest assumption in the repository's external-specification boundary and document the exact missing fact and follow-up, rather than attaching `external_body` to the public lemma.

### `covers` now trusts its executable/specification correspondence

- **Guideline:** `centralize-trusted-boundaries`
- **Location:** `aster_common/src/page_table/page_table_mode.rs:33`
- **Evidence:** The patch adds `#[verifier::external_body]` to `covers`, whose contract is `ensures res == Self::covers_spec(r)` and whose executable body directly computes the two comparisons used by `covers_spec`.
- **Problem:** The correspondence between runtime behavior and the specification is no longer checked, even though both definitions are local and structurally identical. Future edits can silently make the executable predicate diverge from the specification used by verified callers.
- **Suggestion:** Remove `#[verifier::external_body]` and make the existing body verify against `covers_spec`; if unfolding is the obstacle, use a focused reveal/inline proof rather than trusting the whole executable function.

## Low

No low-severity findings.

## Evidence check record

- Read `diff.patch` in full and compared it with both supplied versions of each changed file; the patch contains exactly two added `external_body` annotations and two added trigger annotations.
- Checked the surrounding definitions of `trace`, `trace_empty_is_head`, `trace_no_longer_than_path`, `covers_spec`, `covers`, and the complete body of `lemma_recursive_visit_induction` in the supplied `after/` snapshot.
- The empty-path contradiction is a direct static consequence of the quoted contracts: `seq![self.root.value].len() == 1` and `path.len() == 0` conflict with `self.trace(path).len() <= path.len()`.
- No `#[verifier::rlimit(...)]` change is present, and the patch introduces no external specification for a `std`, `core`, or `alloc` API.
- Per the requested fast-review constraints, repository history, subagent passes, Verus execution, CI, exhaustive rule enumeration, and isolated caller experiments were not performed. Findings are based solely on the authoritative patch and supplied before/after context.
