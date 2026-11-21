# Review: PR 704 snapshot `0ae594a446f7` (fast static review)

## Scope and bottom line

Scope: the authoritative `diff.patch` (326 lines), with the corresponding `before/` and `after/` trees used only for context. The change adds trusted specifications for `BTreeMap::get_mut`, mutable B-tree cursors, and cursor peeking, then re-exports them from `vstd_extra`.

**Bottom line:** Two medium-severity contract issues remain. The same-key (`Key == Q`) path is substantially modeled, but the new heterogeneous borrowed-key surface is not connected to any semantic model, and the cursor peek contracts publish position/map facts without requiring their own model invariant. No `rlimit` change is present.

## High

None.

## Medium

### 1. The heterogeneous borrowed-key contract is opaque and does not constrain the comparison used by the postconditions

**Location:** `verified_libs/vstd_extra/src/external/btree.rs:67-85`, used by the contracts at `:162-230`.

**Rules:** `complete-external-contracts`, `reuse-existing-specifications`, `upstream-reusable-specs`; API preconditions/postconditions.

`borrowed_key_ordering_matches::<Key, Q>()` and `borrowed_key_cmp::<Key, Q>(...)` are two independent uninterpreted functions. The only bridge axioms cover `Q = Key`:

```rust
borrowed_key_ordering_matches::<Key, Key>()
borrowed_key_cmp::<Key, Key>(stored_key, key) == stored_key.cmp_spec(key)
```

For a real heterogeneous lookup such as `BTreeMap<String, _>` queried with `str`, there is no exported fact with which a caller can establish the required predicate, and—more importantly—no clause saying that `borrowed_key_ordering_matches::<Key, Q>()` makes `borrowed_key_cmp` agree with the comparison that `Borrow<Q>` and `Q::cmp` perform. Nevertheless, `lower_bound_mut` and `upper_bound_mut` describe the returned cursor entirely in terms of that unconstrained `borrowed_key_cmp` (`before_lower_bound`/`before_upper_bound`, lines 88-130). Thus the public generic signatures advertise borrowed-key support that is neither dischargeable nor semantically tied to the runtime operation outside the same-key special case.

Define/reuse a semantic `Borrow` model and make the ordering predicate an open property connecting stored-key order, the borrowed value, and `Q`'s comparison; define the bound predicates from that model. If the active vstd cannot express that yet, narrow these specifications to `Q = Key` for now and coordinate the missing general model upstream rather than cementing a second local uninterpreted comparison API.

### 2. `peek_prev` and `peek_next` expose invariant-dependent model facts without requiring a well-formed cursor model

**Location:** `verified_libs/vstd_extra/src/external/btree.rs:234-286`.

**Rule:** `complete-external-contracts`; API preconditions/postconditions and invariants.

Both contracts only state the conditional preservation clause

```rust
old(cursor)@.wf() ==> final(cursor)@.wf()
```

but their `Some`/`None` arms unconditionally interpret `position`, index `keys`, index `map`, and assert boundary equalities such as `position == 0` or `position == keys.len()`. Those facts have the intended cursor meaning only under `CursorMutModel::wf`; outside it, the model does not even guarantee `0 <= position <= keys.len()` or that `keys` and `map` describe the same entries. This matters at a trusted boundary because `view` itself is uninterpreted, while the constructors establish `cursor@.wf()` only behind `obeys_cmp::<Key>()` (lines 199-230).

Require `old(cursor)@.wf()` on both peek specifications, then guarantee `final(cursor)@.wf()` unconditionally. That makes every indexed/model-dependent postcondition rest on an explicit caller obligation and prevents the assume-specification from assigning cursor semantics to states outside its declared invariant.

## Low

None.

## Evidence check record

- Read all 326 lines of `diff.patch`; primary changed file is the new 288-line `verified_libs/vstd_extra/src/external/btree.rs`, plus its module export and the `btree_cursors` feature gate.
- Compared the new file with the `before/` tree (where it is absent) and inspected the `after/` call context in `ostd/src/util/range_alloc.rs:157-178`; that caller uses same-type `usize` keys, so finding 1 does not claim that this existing call site itself needs heterogeneous lookup.
- Checked the standard `BTreeMap` bound semantics against the four `before_lower_bound` / `before_upper_bound` cases; their Included/Excluded directions are consistent for a faithful total comparison.
- Checked mutation framing: `borrowed_key_mutated` attempts to preserve the non-selected remainder, so no separate lost-entry finding is reported.
- Searched the after tree for call sites and axiom-group use. The added specification helpers have no verified consumer in this patch, and `group_btree_extra_axioms` is not used elsewhere in the captured tree.
- Searched the patch for `#[verifier::rlimit(...)]`; none is added or changed, so the numeric cap is not implicated.
- The new specifications are generally useful standard-library contracts in `vstd_extra`; the recommendation in finding 1 incorporates the required upstreaming/discussion path rather than creating a duplicate standalone workflow finding.

## Verification disclosure

Per the fast-review override, this review did **not** inspect Git history, run Verus, build the crate, or run isolated caller/contract experiments. Findings are static, evidence-backed contract review of the captured patch and before/after context only.
