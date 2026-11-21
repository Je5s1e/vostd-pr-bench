# Review: `diff.patch` (`before` → `after` snapshot)

> Produced from the VOSTD proof-engineering and API-contract criteria.
> Scope: the 45-line patch to `lock-protocol/src/mm/page_table/node/entry.rs`, with the supplied `before` and `after` files used for context.

**Bottom line:** This change removes `#[verifier::external_body]`, but it does not actually verify `alloc_if_none`: the body still establishes its obligations through `assume`, and the newly added assumptions include a proposition that directly contradicts the function's own precondition. The contract and implementation also disagree about whether the target entry already exists, so the advertised `Some` result is proved only by declaring the `None` path impossible. These are blocking trust and API-contract defects.

## High

### H1 — The proof assumes a fact contradicted by the function precondition

**Guideline:** `centralize-trusted-boundaries`  
**Location:** `lock-protocol/src/mm/page_table/node/entry.rs:374`, `:383`, `:427-445`

**Quoted evidence:**

```rust
old(spt).i_ptes.value().contains_key(old(self).pte.pte_paddr() as int),
```

but, before any update to `spt.i_ptes`, the new proof block says:

```rust
assume(!spt.i_ptes.value().contains_key(self.pte.pte_paddr() as int));
```

Between these statements the body only reads the node level and allocates through `&mut spt.alloc_model`; it does not update `spt.i_ptes`, `self`, or `self.pte`. Thus the added assumption contradicts the entry-state fact required on entry and makes the proof context inconsistent. Once that happens, the state-machine transition and all later postconditions can be discharged without establishing them. The other new `assume` statements (`i_pte.wf()`, root/level relationships, and frame level) likewise keep the proof dependent on unproved local trust even though the patch presents the function as no longer external.

**Suggestion:** Correct the entry-state precondition first (the `set_child` transition evidently needs the target address absent), then replace every added `assume` with assertions or lemmas derived from `Entry::wf`, `SubPageTable::wf`, the allocation contract, and the node-level contract. Keep the function trusted until those obligations are genuinely proved; merely moving trust from `external_body` into its body is not a verification improvement.

### H2 — The result contract is proved by assuming away its contradictory runtime branch

**Guideline:** `api-preconditions`, `api-postconditions`  
**Location:** `lock-protocol/src/mm/page_table/node/entry.rs:393`, `:415-418`

**Quoted evidence:**

```rust
ensures
    // ...
    res is Some,
```

while the executable body contains:

```rust
if !self.pte.is_present() {
    assume(false);
    // The entry is already present.
    return None;
}
```

The condition, comment, return value, function name, and unconditional `res is Some` guarantee do not form a coherent API. In particular, no checked fact connects `!self.pte.is_present()` to `false`; the branch is accepted only because `assume(false)` gives the verifier arbitrary facts. Removing `external_body` therefore exposes no usable proof that the publicized postcondition matches runtime behavior.

**Suggestion:** Decide the intended semantics and express them consistently. If this routine allocates only for an absent entry, make the absence condition a proved precondition (or return `None` for an already-present entry) and align the branch direction and postcondition. If legal calls must always see a present entry and always return `Some`, prove `self.pte.is_present()` from the preconditions and delete the branch and `assume(false)`; do not encode the missing connection as an assumption.

## Medium

None.

## Low

None.

## Evidence check record

- Read `diff.patch` in full and compared the complete supplied `before` and `after` context around `Entry::wf` and `alloc_if_none`.
- Checked the key premise for H1 against the exact mutation sequence: before the contradictory assumption, the only mutable borrow is of `spt.alloc_model`; there is no write to `spt.i_ptes`, `self`, or `self.pte`.
- Checked H2 against the exact contract and executable branch: `res is Some` and `return None` coexist, with `assume(false)` as the only local justification.
- No `#[verifier::rlimit(...)]` change and no new or materially changed `std`/`core`/`alloc` external specification appear in the patch.
- No new spec/model was introduced, so no spec-reuse finding is supported by this patch.
- Per the requested fast, non-exhaustive review, commit history, exhaustive rule enumeration, sub-agent passes, Verus/CI verification, and isolated caller experiments were not run. Findings are based on static source evidence only.
