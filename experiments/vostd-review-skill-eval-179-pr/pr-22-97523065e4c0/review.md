# Review: `diff.patch` (`before` → `after`)

> Produced from the supplied VOSTD review criteria and the skill's API-contract criteria.
> Scope: the authoritative `pr-22-97523065e4c0/diff.patch`, with `before/` and `after/` used only as surrounding context.

**Bottom line:** Replacing `admit()` with a checked proof is a meaningful reduction of the trusted surface, and the patch does not change the lemma's public contract. The new proof should nevertheless be simplified before merge: most of its arithmetic block manually establishes child validity even though the existing trace round-trip lemma, already called later in the same proof, supplies that result directly. No API-contract, invariant, new-assumption, external-specification, or excessive-rlimit defect was found in this fast static pass.

## High

No high-severity findings.

## Medium

### Reuse the existing trace round-trip instead of reproving child bounds

- **Guidelines:** `reuse-existing-specifications`, `document-real-proof-debt`, `use-chained-comparisons`, `avoid-redundant-as-int-casts`
- **Location:** `lock-protocol/src/spec/utils.rs:813`
- **Evidence:** The new proof spends lines 813–861 on a separate `dep`/`level`/`sz_dep` calculation and an arithmetic chain ending in:

  ```rust
  assert(nid + offset * (sz as int) + 1 < Self::total_size()) by {}
  ```

  Yet the same proof later calls:

  ```rust
  assert(Self::nid_to_trace(child) == trace.push(offset)) by {
      Self::lemma_trace_to_nid_from_root(trace.push(offset));
  };
  ```

  `lemma_trace_to_nid_from_root` already ensures both `Self::valid_nid(nid)` and `trace =~= Self::nid_to_trace(nid)` for its returned node (`utils.rs:566–572`). Together with `lemma_trace_to_nid_increment(trace, offset)`, this is exactly the existing abstraction needed to identify `get_child(nid, offset)` and establish that it is valid. The manual block also introduces the non-guideline forms `0 <= dep && dep < 4` and numerous defensive `(sz as int)` casts, plus comments that mostly narrate adjacent assertions.
- **Problem:** Reconstructing the same validity fact through low-level tree-size arithmetic makes the proof longer and more sensitive to representation changes while duplicating an existing verified interface. The extra narration, split comparisons, and casts compound the review burden without strengthening the lemma's contract.
- **Suggestion:** Obtain `trace` with `lemma_nid_to_trace`, establish `valid_trace(trace.push(offset))` from `nid_to_dep(nid) < 3` and `valid_pte_offset(offset)`, invoke `lemma_trace_to_nid_increment`, then bind the result of `lemma_trace_to_nid_from_root(trace.push(offset))`. Use those two lemma postconditions to show that result equals `get_child(nid, offset)` and to discharge validity, parent, and offset round trips. Remove the duplicated `dep`/`level`/tree-size block; in any remaining bounds use chained comparisons and retain only casts Verus actually requires.

## Low

No low-severity findings.

## Evidence check record

- Treated `pr-22-97523065e4c0/diff.patch` (90 lines) as the immutable authoritative change and used the matching complete `before/` and `after/` source files for numbered context.
- Confirmed that the only changed code replaces `admit()` in `NodeHelper::lemma_get_child`; the lemma's `requires` and `ensures` are unchanged.
- Checked the nearby definitions and exact signatures of `get_child`, `lemma_nid_to_trace`, `lemma_trace_to_nid_increment`, and `lemma_trace_to_nid_from_root`. The last lemma guarantees both node validity and the trace/node round trip.
- Checked the suggested reuse path against the changed proof's types and conditions: `trace` is a `Seq<nat>`, `offset` is a `nat`, and the original preconditions provide the depth and offset bounds needed for `valid_trace(trace.push(offset))`.
- No `assume`, `external_body`, axiom, or new `admit` is introduced. The patch removes one `admit`; remaining admits elsewhere in the context are unchanged and outside reporting scope.
- No `#[verifier::rlimit(...)]` change appears, so the `rlimit > 200` workflow check did not trigger. No new or materially changed external specification for a `std`, `core`, or `alloc` API appears.
- The public proof API's preconditions and postconditions are unchanged and remain aligned with `get_child`, `get_parent`, and `get_offset`; no separate `api-preconditions` or `api-postconditions` finding was supported.
- **Verification disclosure:** Per the fast-review constraint, no Verus run, caller experiment, repository-history analysis, sub-agent pass, or exhaustive guideline checklist was performed. Conclusions and the suggested simplification are based on static patch and before/after-context evidence only.
