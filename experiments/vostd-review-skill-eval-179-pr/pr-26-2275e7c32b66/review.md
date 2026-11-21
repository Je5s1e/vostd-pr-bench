# Review: PR #26 captured diff

> Fast isolated VOSTD review of `diff.patch`, using the captured `before/` and `after/` trees for context.
> Scope: `lock-protocol/src/test/rw_version/spec/tree.rs`, `vstd_extra/src/map_extra.rs`, and `vstd_extra/src/seq_extra.rs` as changed by the supplied patch. Per the review override, no repository history, Verus run, caller experiment, or exhaustive checklist was performed.

**Bottom line:** The patch adds useful support for the `read_lock` invariant, but the edited inductive proof still closes its quantified obligation with `admit()`, so the central preservation argument remains trusted rather than proved. It also adds two public map-filter lemmas with no caller or documented external consumer in the captured after-tree. No changed `#[verifier::rlimit]` was found, and the patch adds no external specification of a `std`, `core`, or `alloc` API.

## High

None.

## Medium

### The edited invariant proof still relies on `admit()`

- **Guideline:** `centralize-trusted-boundaries`
- **Location:** `lock-protocol/src/test/rw_version/spec/tree.rs:336`
- **Evidence:** After splitting on `id != nid` and adding supporting lemmas, the body of the quantified preservation proof still ends with `admit();`. This obligation establishes `post.rc_cursors_relation()` for the `read_lock` transition (lines 301–337).
- **Problem:** `admit()` makes the state-machine invariant preservation claim trusted at its use site. The base snapshot already had an admit in this inductive proof, so this does not enlarge the pre-existing trusted surface, but the materially rewritten proof still does not verify the claimed invariant.
- **Suggestion:** Finish both branches without `admit()`. In the `id == nid` branch, connect the remove/insert filter equalities to the filtered-map length change; in the other branch, use `lemma_insert_value_filter_same_len` to close the unchanged-count equality.

### Remove or justify the newly unused public proof helpers

- **Guideline:** `avoid-unused-spec-helpers`
- **Locations:** `vstd_extra/src/map_extra.rs:46`, `vstd_extra/src/map_extra.rs:125`
- **Evidence:** The patch adds `pub proof fn lemma_value_filter_contains` and `pub proof fn lemma_insert_value_filter_different_len`. A name-based search of the complete captured `after/` tree finds no call to either function; the only hits are their definitions. Neither has documentation identifying an intentional external consumer or abstraction boundary.
- **Problem:** These helpers expand the public proof API without serving the proof changed by this patch. In particular, `read_lock_inductive` uses `lemma_insert_value_filter_same_len`, not the new `different_len` lemma.
- **Suggestion:** Delete both helpers until a caller is added, or add the concrete caller in this change. Retain a public helper without an in-tree caller only if it is an intentional external API and document that consumer/boundary.

## Low

None.

## Evidence check record

- Read `diff.patch` in full and compared all three captured before/after files around the changed code.
- Searched the captured after-tree for calls to the added map helpers. `lemma_map_insert_len` and `lemma_map_remove_len` have callers; `lemma_value_filter_contains` and `lemma_insert_value_filter_different_len` do not.
- Inspected trust-affecting additions. The patch retains/adds one `admit()` in the materially edited `read_lock_inductive` proof and invokes existing VSTd axioms, but introduces no new axiom declaration, `assume`, or `external_body`.
- Inspected the patch and after-tree for `#[verifier::rlimit]`; none was found, so the `rlimit > 200` workflow check is not triggered.
- The changed APIs are proof lemmas over VSTd `Map`/`Seq`; no external specification for a `std`, `core`, or `alloc` API was added or materially changed, so the upstreamable-external-spec workflow check is not triggered.
- `lemma_insert_value_filter_different_len` calls `lemma_map_insert_len(m, k, v)` in its `f(v)` branch (`map_extra.rs:145`), although the postcondition concerns `value_filter(m, f)`. This call is visibly unrelated to the filtered-map length; because Verus verification was explicitly excluded, the review does not claim that the function fails verification and does not elevate this observation to a separate finding.
- **No-verification disclosure:** No Verus invocation, build, test, isolated client, or controlled variant was run. Findings are based solely on static evidence in the supplied snapshot, so proof acceptance and solver behavior remain unverified.
