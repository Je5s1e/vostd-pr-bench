# Review: PR 419 snapshot `e2a32e9a225f` (fast static review)

## Scope and bottom line

Fast isolated review of `diff.patch`, with the corresponding `before/` and `after/` source used for context and line locations. The change substantially expands the page-table ghost model, but it also introduces one contract that is directly contradicted by its executable body, two new axioms in place of a missing accounting invariant, and three changed proof limits above VOSTD's cap. Bottom line: **do not merge until the `try_traverse_and_lock_subtree_root` contract is made truthful**; the added trust and proof-limit debt should also be addressed.

**Bottom line:** Do not merge until the `try_traverse_and_lock_subtree_root` contract is made truthful; the added trust and proof-limit debt should also be addressed.

## High

### 1. `try_traverse_and_lock_subtree_root` promises `Some` although its body still returns `None`

**Rules:** `complete-external-contracts`; API postconditions / trusted-boundary soundness.

**Evidence:** [`ostd/src/mm/page_table/cursor/locking.rs:185`](after/ostd/src/mm/page_table/cursor/locking.rs#L185) adds the unconditional postcondition `r is Some` to an `#[verifier::external_body]` function. The executable body has two reachable stray-node branches returning `None`, at [`locking.rs:285`](after/ostd/src/mm/page_table/cursor/locking.rs#L285) and [`locking.rs:338`](after/ostd/src/mm/page_table/cursor/locking.rs#L338). The function's own documentation immediately above still says that a stray node causes `None` and that the caller should retry. `lock_range` no longer retries and instead unconditionally calls `unwrap()` at [`locking.rs:90`](after/ostd/src/mm/page_table/cursor/locking.rs#L90).

This is both a false trusted specification and a runtime panic path under the documented stray-node race. The comment claiming that the shipped body is a “post-retry form” does not match the shipped body.

**Suggested correction:** restore `r is Some ==> ...`, restore the retry loop in `lock_range`, and specify/prove the state relation across a `None` result so retries are legal. Alternatively, change the executable external body to actually perform the retry before making `r is Some` unconditional.

## Medium

### 1. Child-count safety is asserted by two local axioms instead of represented by the node invariant

**Rules:** `centralize-trusted-boundaries`; `implement-inv-for-models`.

**Evidence:** [`ostd/specs/mm/page_table/node/owners.rs:136`](after/ostd/specs/mm/page_table/node/owners.rs#L136) and [`owners.rs:147`](after/ostd/specs/mm/page_table/node/owners.rs#L147) add public axioms stating that an absent PTE implies `nr_children < NR_ENTRIES` and a present PTE implies `nr_children > 0`. They are used to justify executable `+ 1` and `- 1` counter updates in `Entry::replace`. The accompanying comment explicitly says the intended invariant is that `nr_children` counts present PTEs, but that invariant is not modeled or maintained; the boundary facts are simply trusted beside their caller.

These axioms can mask drift between the counter and `children_perm`, precisely the relationship needed to justify the arithmetic. Because they are generic over every `PageTableConfig` and have no external implementation whose behavior they specify, they enlarge the trusted logical base.

**Suggested correction:** add the count relationship (or an equivalent inductively maintainable accounting predicate) to `NodeOwner::inv`, establish it at construction, and preserve it at every PTE mutation. Then derive both bounds as ordinary proof lemmas. If temporary trust is unavoidable, isolate and clearly gate it at a dedicated trust boundary rather than exposing generic public axioms on `NodeOwner`.

### 2. Three changed `rlimit` values exceed the project cap of 200

**Rule:** `decompose-before-raising-rlimit`.

**Evidence:** the diff changes/adds `#[verifier::rlimit(10000)]` on [`ostd/specs/mm/page_table/cursor/owners.rs:1142`](after/ostd/specs/mm/page_table/cursor/owners.rs#L1142), `#[verifier::rlimit(1200)]` on [`ostd/src/mm/page_table/cursor/mod.rs:2519`](after/ostd/src/mm/page_table/cursor/mod.rs#L2519), and `#[verifier::rlimit(1000)]` on [`cursor/mod.rs:2852`](after/ostd/src/mm/page_table/cursor/mod.rs#L2852). Each is above the workflow guideline's maximum of 200; two are increases from already excessive values (8000 to 10000 and 400 to 1000).

**Suggested correction:** decompose the affected proofs and keep every changed cap at or below 200.

## Low

No strong low-severity findings.

## Evidence check record

- Confirmed the `r is Some` contradiction by reading the full after-context of the external-body function and comparing its contract, documentation, two `return None` branches, and the changed `lock_range` caller against `before/`.
- Confirmed both child-count axioms are newly introduced in the diff and traced their use to the executable counter updates in `Entry::replace`.
- Confirmed all three listed `rlimit` attributes are changed by this patch and exceed the skill's workflow threshold of 200.
- Checked the diff for newly added `assume`, `admit`, `axiom`, `external_body`, and `rlimit` trust markers. The consolidated `assume` in `lock_range` replaces four pre-existing admits, so it is not reported as a net-new trust finding; the false external-body postcondition is the material regression.

## Verification disclosure

Per the fast-review override, no Verus build, proof verification, history analysis, isolated caller experiment, or exhaustive guideline checklist was run. Findings are based on static inspection of `diff.patch` and the supplied before/after source snapshots.
