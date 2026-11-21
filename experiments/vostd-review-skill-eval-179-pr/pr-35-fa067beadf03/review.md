# Review: isolated `diff.patch` with bundled before/after context

> Produced from the VOSTD review skill's maintainability, proof-engineering, and API-contract criteria.
> Scope: fast, non-exhaustive static review of `diff.patch` and the corresponding files under `before/` and `after/`.

**Bottom line:** The change still admits the central write-lock invariant after the `write_lock` transition and adds a second admitted helper theorem, so the new locking argument is not actually established by Verus. In addition, the two new map-insertion lemmas formally expose only the reverse of the implication promised by their documentation, preventing callers from using the lemmas to construct the advertised `forall_map` facts. These issues should be fixed before merge.

## High

### The new write-lock invariant is trusted rather than proved

- **Guideline:** `centralize-trusted-boundaries`
- **Location:** `lock-protocol/src/test/rw_version/spec/tree.rs:475`
- **Evidence:**

  ```rust
  assert(post.inv_write_lock_cursors_subtree_locked()) by {
     admit();
  }
  ```

  The patch changes the inductiveness obligation from `post.inv_non_overlapping()` to the stronger, newly introduced `post.inv_write_lock_cursors_subtree_locked()`, but continues to discharge the changed obligation with `admit()`. This invariant states that every write-lock cursor points to a `WriteLocked` node whose descendants have neither readers nor write locks; trusting it bypasses the core exclusion property that the PR is restructuring.

  **Suggestion:** Prove `post.inv_write_lock_cursors_subtree_locked()` from the `write_lock` transition requirements and the pre-state invariants. In particular, establish that the selected node has zero readers and that no descendant is read- or write-locked, then use the cursor update lemmas to preserve the predicate for all other cursors. Do not keep this proof debt in an inductiveness check.

## Medium

### A new subtree/accounting theorem is introduced with `admit()`

- **Guideline:** `centralize-trusted-boundaries`
- **Location:** `lock-protocol/src/test/rw_version/spec/tree.rs:588`
- **Evidence:**

  ```rust
  proof fn lemma_read_counter_zero_implies_subtree_zero(&self, nid: NodeId, child: NodeId)
  ...
  ensures
      self.reader_counts[child] == 0,
  {
      ...
      admit();
  }
  ```

  This is a new logical fact about reader-count propagation, and its unchecked postcondition becomes available to later proofs even though the current patch does not derive it. The commented-out proof sketch immediately above the `admit()` does not constrain that trusted fact.

  **Suggestion:** Complete the contradiction proof: if `child` has a positive count, use `inv_reader_counts_cursors_relation` to obtain a cursor whose read path contains `child`, use the cursor/path invariant plus `in_subtree_range(nid, child)` to show that the same path contains `nid`, and derive a positive count for `nid`. If that implication needs an additional path-ordering premise, add it explicitly rather than admitting the stronger theorem.

### The insertion lemmas do not provide the documented construction direction

- **Guideline:** `api-postconditions`
- **Locations:** `vstd_extra/src/map_extra.rs:250`, `vstd_extra/src/map_extra.rs:279`
- **Evidence:** The documentation says that the inserted-map property “holds if” the old-map property and the inserted value's predicate hold, but both contracts state only the converse:

  ```rust
  /// `forall_map(m.insert(k, v), f)` holds if `f(k, v)` holds and ...
  ensures
      forall_map(m.insert(k, v), f) ==> f(k, v) && ...

  /// `forall_map_values(m.insert(k, v), f)` holds if `f(v)` holds and ...
  ensures
      forall_map_values(m.insert(k, v), f) ==> f(v) && ...
  ```

  Thus a natural caller that knows `f(k, v)`/`f(v)` and the appropriate old-map predicate cannot derive `forall_map(m.insert(k, v), f)` or `forall_map_values(m.insert(k, v), f)`. That is the direction needed to preserve a universal map invariant across insertion and the direction explicitly promised by the API comments.

  **Suggestion:** Make each postcondition an equivalence, matching the neighboring remove lemmas, or add the missing forward implication as a separate `ensures` clause and prove it. For example, use `forall_map(m.insert(k, v), f) <==> f(k, v) && if m.contains_key(k) { forall_map(m.remove(k), f) } else { forall_map(m, f) }`, with the analogous value-only form.

## Low

No strong low-severity findings.

## Evidence check record

- Read all 1,021 lines of `diff.patch` and inspected the complete bundled before/after versions of all six changed files.
- Compared the changed trust sites against the before image. The three one-line inductiveness `admit()` bodies for `write_unlock`, `allocate`, and `deallocate`, plus the unrelated `common.rs` admit, predate this patch and were not reported. The `write_lock` proof already had an `admit()`, but this patch changes the proposition trusted at that site to the new subtree-lock invariant; the new helper at line 588 adds a separate trusted theorem.
- Checked the new map contracts against their exact comments and against the adjacent `lemma_forall_map_remove`/`lemma_forall_map_values_remove` equivalence contracts. No experiment was needed to establish the missing implication direction.
- No `#[verifier::rlimit(...)]` change appears in the patch, so there is no value over the workflow cap of 200 to report. No new or materially changed external specification for a `std`, `core`, or `alloc` API appears in scope.
- A limited name search found no earlier `forall_map` definition in this PR's `before/` image. This fast pass did not perform the skill's exhaustive repository-wide spec-reuse search.
- **No-verification disclosure:** Per the requested fast-review constraints, this review used no Git history, sub-agents, Verus execution, CI rerun, or isolated caller experiment. The isolated bundle does not contain the repository's live coding-guideline pages, so findings use the guideline IDs and criteria embedded in `.codex/skills/vostd-code-review`; conclusions are static and non-exhaustive.
