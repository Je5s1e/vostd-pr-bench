# Review: PR 26 snapshot `5474cd472251`

> Fast, non-exhaustive VOSTD review of `diff.patch`, with `before/` and `after/` used only for context.
> Scope: the captured changes under `pr-26-5474cd472251`; no repository history, Verus run, caller experiment, or exhaustive guideline checklist was performed.

**Bottom line:** The patch is not ready to merge because it introduces or promotes several `admit()`-backed facts into code that other proofs can consume, including a regression in a previously non-admitted lemma. Separately, the new filtered-map length proof invokes its key cardinality lemma on `m` rather than `value_filter(m, f)`, so that call does not establish the claimed branch result. No changed `#[verifier::rlimit(...)]` or new external specification for a `std`, `core`, or `alloc` API appears in the captured diff.

## High

### Trusted facts are added to ordinary proof modules

- **Guideline:** `centralize-trusted-boundaries` (also conflicts with the explicit authorization rule for new `admit` under `preserve-exec-code`)
- **Locations:** `lock-protocol/src/test/rw_version/spec/common.rs:135`, `lock-protocol/src/spec/utils.rs:585`, `lock-protocol/src/test/rw_version/spec/tree.rs:397`
- **Evidence:** The patch adds `admit();` inside `lemma_wf_tree_path_nid_increasing`; the captured `before` version of that lemma has no admission. It also moves the admitted public `lemma_level_dep_relation` from the test-local `spec/utils.rs` into shared `lock-protocol/src/spec/utils.rs`, and adds an admitted `lemma_rc_cursors_relation_implies_rc_positive` whose contract promises `s.rc_positive(path)`.
- **Problem:** These statements become trusted theorem facts rather than checked proofs. In particular, this is not just unchanged pre-existing debt: one previously non-admitted lemma regresses, a test-local admitted theorem is promoted to the shared specification module, and a new admitted lemma is added. Any downstream proof can rely on their postconditions without establishing them.
- **Suggestion:** Remove the new admissions before merge. Restore a checked proof for `lemma_wf_tree_path_nid_increasing`; keep the moved level helper test-local until it is proved (its postcondition follows directly from the definitions and bounds); and delete the unused `lemma_rc_cursors_relation_implies_rc_positive` or add it only together with a complete proof. The already-admitted state-machine cases should remain explicitly tracked as existing proof debt rather than being presented as newly completed proofs.

## Medium

### Filtered-map cardinality lemma is called on the wrong receiver

- **Guideline:** `reuse-existing-specifications`
- **Location:** `vstd_extra/src/map_extra.rs:145`
- **Evidence:** In the `f(v)` branch of `lemma_insert_value_filter_different_len`, the target is `value_filter(m.insert(k, v), f).len() == value_filter(m, f).len() + 1`, but the proof calls `lemma_map_insert_len(m, k, v)`. The same file shows that `lemma_map_insert_len` proves a fact only about the exact map passed as its first argument; the sibling same-length proof correctly calls it as `lemma_map_insert_len(value_filter(m, f), k, v)` at line 118.
- **Problem:** Since the preconditions also give `m.contains_key(k)`, the current call establishes that inserting into `m` does not change `m.len()`; it says nothing about inserting `k` into the filtered map. The needed fact is that `k` is absent from `value_filter(m, f)` when `f(m[k])` is false and `f(v)` is true.
- **Suggestion:** First establish `!value_filter(m, f).contains_key(k)` (the new `lemma_value_filter_contains` has exactly the relevant contract), then call `lemma_map_insert_len(value_filter(m, f), k, v)`.

## Low

| Finding | Guideline | Detail |
|---|---|---|
| Remove checked-in abandoned proof attempts | `document-real-proof-debt` | `lock-protocol/src/test/rw_version/spec/tree.rs:346` and `:357`, plus `:408`, add large commented-out proof bodies immediately beside active admissions. They recount unfinished attempts rather than a current constraint or a concrete TODO. Delete them, or replace them with one short TODO naming the exact remaining obligation. |

## Evidence check record

- Read all 1,336 lines of the captured `diff.patch` and inspected the corresponding `before/` and `after/` regions for every reported location.
- Confirmed the regression in `lemma_wf_tree_path_nid_increasing`: `before/.../common.rs:116-136` contains no `admit`, while `after/.../common.rs:117-138` adds one at line 135.
- Confirmed that `lemma_level_dep_relation` was admitted in the deleted test-local helper and remains admitted after being copied into the shared specification helper; the finding is about promotion of that trusted fact, not a claim that its theorem statement is newly invented.
- Checked the local signatures of `lemma_map_insert_len`, `lemma_value_filter_contains`, and both filtered-map length lemmas. The suggested correction preserves the original conditions and uses the receiver whose length occurs in the goal.
- Static search found no changed `rlimit`, `assume_specification`, `external_body`, or `#[verus_spec]` entry in the patch.
- The expected live `docs/coding-guidelines/{README,maintainability,proof-engineering,workflow}.md` files are absent from this isolated workspace root. Guideline IDs were therefore checked against the bundled VOSTD review skill/personas and the available captured maintainability guideline snapshot; this limits checklist coverage but not the quoted code evidence above.
- **No-verification disclosure:** Per the requested fast override, I did not run Verus, CI, build commands, standalone proof experiments, or targeted caller/client experiments. Verification status is unknown; the review is based on static source evidence only.
