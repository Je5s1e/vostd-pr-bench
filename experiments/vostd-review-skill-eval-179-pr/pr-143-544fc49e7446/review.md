# Review: `diff.patch` (`d888930f85df1e81da67cb4f5580d183a4115f1e..544fc49e744600241357a7f66e3e54ea9b8bb6ca`)

> Produced from the supplied immutable diff and before/after context, using the VOSTD proof-engineering and API-contract review criteria.
> Scope: fast, non-exhaustive static review of `pr-143-544fc49e7446/diff.patch` (SHA-256 `2ae9ef0b489a939d2d8c59269b1dcb04268236459472cca408833e877754f221`). No history review, Verus run, caller experiment, or exhaustive guideline pass was performed.

**Bottom line:** This change is not ready to merge because it replaces checked state-machine and lock-protocol reasoning with a large new trusted surface. Most importantly, the new stray map has a concrete lifecycle hole: deallocation retains a `(nid, paddr) => true` entry, while reallocation of that same address admits the map-insertion freshness obligation. The remaining new `admit()` calls also make the public lock and PTE-state postconditions depend on unchecked local assertions.

## High

### The new stray-map lifecycle and lock proofs are accepted through `admit()`

- **Guideline:** `centralize-trusted-boundaries`
- **Locations:** `lock-protocol/src/spec/rcu/tree.rs:281`, `lock-protocol/src/spec/rcu/tree.rs:337`, `lock-protocol/src/spec/rcu/tree.rs:363`; supporting call-path admissions at `lock-protocol/src/exec/rcu/cursor/locking.rs:564`, `lock-protocol/src/exec/rcu/node/spinlock/mod.rs:676`, and `lock-protocol/src/exec/rcu/node/mod.rs:475`.
- **Quoted evidence:** allocation performs `add strays += [ (nid, paddr) => false ] by { admit(); };`; deallocation performs `remove strays -= [ (nid, paddr) => false ];` followed by `add strays += [ (nid, paddr) => true ];`. All newly changed inductive hooks, including `protocol_lock_inductive`, `normal_lock_inductive`, and `normal_deallocate_inductive`, have bodies `{ admit(); }`. The executable proof path additionally states `assert(m.node_is_locked(cur_node.nid())) by { admit(); };` and `assert(NodeHelper::in_subtree_range(m.sub_tree_rt(), self.nid@)) by { admit(); };`.
- **Problem:** A legal allocate/deallocate/reallocate cycle may reuse the same `(nid, paddr)`. The first deallocation leaves that key in `strays` with value `true`; the next `add` needs the key to be fresh, but the change proves that requirement only by admission. More broadly, admitting every affected inductiveness proof means `TreeSpec::inv()` and the lock APIs' `ensures` can be consumed downstream without Verus having established that the changed transitions preserve the new invariants.
- **Suggestion:** Define a sound address-reuse lifecycle before proving the transitions—for example, remove retired `true` entries when their identity is no longer needed, or key generations/allocations with a fresh identity rather than a reusable physical address. Then replace the two map-insertion admissions, every changed `#[inductive(...)]` admission, and the local lock/PTE admissions with checked lemmas. Do not expose the strengthened `stray_is_false`, `SpinGuard::wf`, or lock postconditions until those proofs close without `admit()`.

## Medium

None.

## Low

None.

## Evidence check record

- Read `diff.patch` in full and used the supplied `before/` and `after/` files only for surrounding line-level context.
- Searched the scoped diff for `admit`, `external_body`, and `rlimit`. No added or changed `#[verifier::rlimit(...)]` was present, and no `std`/`core`/`alloc` external specification was added or materially changed.
- Refutation check: the deallocation transitions demonstrably preserve the same `(nid, paddr)` key as `true`, while the allocation transitions add that exact key and discharge the insertion side condition with `admit()`. No scoped invariant or precondition requires a never-before-used `paddr` or removes old `true` keys.
- The repository snapshot does not contain live `docs/coding-guidelines/{README,maintainability,proof-engineering,workflow}.md` at its root, so this fast review applied the checked-in review skill's named proof-engineering criterion and records that limitation rather than claiming a full current-guideline audit.
- **No-verification disclosure:** Per the requested fast mode, Verus and Z3 were not run, CI was not repeated, no modified client was constructed, and no historical rationale or exhaustive caller/spec-reuse search was performed. The finding is based on static source evidence and remains subject to normal verification after correction.
