# Review: PR #161 (`c1d63c7e77da5f3cacf16271b5e1da3f05e66adf..fa698a4e527004be4da310b35b4db2dcbb5c09b5`)

> Scope: `diff.patch` and the captured before/after versions of the three changed files. Review criteria were maintainability, proof/trust engineering, assumptions, API contracts, invariants, `rlimit > 200`, and reusable specifications.

**Bottom line:** This change does not establish `protocol_allocate` inductiveness without trust: it adds an `admit()` for a claim contradicted by the protocol's own deallocation history, and it `assume()`s an invariant whose address parameter is shadowed. Both are blocking because they can certify unreachable or false protocol states as invariant-preserving. No API-contract, `rlimit > 200`, or spec-reuse issue was found independently of these trust failures.

## High

### The allocation proof admits a false empty-history claim

- **Guideline:** `centralize-trusted-boundaries`
- **Location:** `lock-protocol/src/spec/rcu/tree.rs:1252`
- **Evidence:** The proof adds `assert(pre.strays_filter(node_id).dom() =~= Set::<(NodeId, Paddr)>::empty()) by {admit();}`. But `protocol_deallocate` removes `(nid, paddr) => false` and immediately adds `(nid, paddr) => true` at lines 332–333. A legal allocate/deallocate/reallocate history therefore reaches allocation with a nonempty `strays_filter(nid).dom()`, even though it has no `false` entry.
- **Problem:** The admitted assertion is stronger than the invariant needed at this point and is not true for reachable states. Once admitted, it can erase retained stray history logically and make the remainder of the inductiveness proof vacuous or inconsistent.
- **Suggestion:** Prove only that the pre-state contains no `false` stray for `nid`, using `pre.inv_pte_is_void_implies_no_false_strays()` together with the allocation precondition `pte_array.is_void(offset)`. Then show that adding `(nid, paddr) => false` makes the filtered set a singleton while preserving any existing `true` entries; remove the `admit()`.

### The proof assumes an invariant whose address comparison is shadowed and generally false

- **Guideline:** `centralize-trusted-boundaries`
- **Location:** `lock-protocol/src/spec/rcu/tree.rs:1315`
- **Evidence:** The new proof ends with `assume(post.inv_stray_has_false_implies_pte_is_alive());`. In that invariant, the quantified address is named `pa` at line 136, but line 141 shadows it with `let pa = NodeHelper::get_parent(nid);`; line 145 consequently requires `get_paddr(offset) == pa`, comparing the PTE address with the parent node ID rather than with the quantified stray address. Allocation writes `PteState::Alive(paddr)` and `(nid, paddr) => false` at lines 311 and 314, so the intended post-state does not establish the shadowed equality in general.
- **Problem:** The `assume()` hides a concrete specification defect at the exact inductive boundary this patch claims to prove. Verification after this point may rely on a false correspondence between stray addresses and live PTEs.
- **Suggestion:** Rename the quantified address to `paddr`, keep the parent as `pa`, compare `get_paddr(offset) == paddr`, and replace the `assume()` with a proof from the transition relation and pre-state invariants. Prove `inv_pte_is_void_implies_no_false_strays` similarly rather than retaining the adjacent assumption at line 1316.

## Medium

No medium-severity findings.

## Low

No low-severity findings.

## Evidence check record

- Read the complete 254-line `diff.patch` and the captured before/after context for all three changed files.
- Traced the new invariant, `protocol_allocate`, `protocol_deallocate`, and the complete changed inductiveness proof. The allocate/deallocate/reallocate counterexample above follows directly from lines 302–314 and 319–333; it does not depend on solver behavior.
- Checked the patch for changed `#[verifier::rlimit(...)]`, `external_body`, and `assume_specification` declarations; none are present. The new helper `lemma_parent_offset_uniqueness` has a direct caller in this patch and no evidence-backed reuse violation was identified.
- The snapshot does not contain its own `docs/coding-guidelines` tree, so rule grounding used the bundled VOSTD review skill's trust-boundary criterion and available captured source evidence.
- **No verification disclosure:** Per the fast-review scope, no Verus run, CI run, proof experiment, caller experiment, repository-history analysis, or exhaustive guideline pass was performed. Findings are static, evidence-backed review conclusions from the supplied patch and before/after files.
