# Review: PR #499 authoritative `diff.patch` (before/after snapshot)

> Produced from the VOSTD maintainability/proof-engineering rules and API-contract criteria.
> Scope: `pr-499-2d320cbb55fc/diff.patch`, with `before/` and `after/` used only for surrounding context and final line numbers.

**Bottom line:** The change introduces two local `assume` statements to satisfy new `PageTableEntryTrait` preconditions. One sits on the caller-visible page-protection path even though that API does not require its closure to produce a property accepted by `set_prop`; the other hides the corresponding obligation when converting a `Child::Frame`. These assumptions make the new verification results depend on facts that the checked contracts do not establish, so they should be removed before merge and replaced with explicit, propagated invariants or preconditions.

## High

### The protection API assumes, rather than specifies, that the closure result is a valid PTE property

- **Guidelines:** `centralize-trusted-boundaries`, `api-preconditions`
- **Location:** `ostd/src/mm/page_table/node/entry.rs:263` (caller-visible entry point at `ostd/src/mm/page_table/cursor/mod.rs:3642`)
- **Evidence:** `Entry::protect` computes `let new_prop = op(prop);` and then adds `assume(self.pte.set_prop_req(new_prop));` immediately before `self.pte.set_prop(new_prop)`. The x86 implementation defines that requirement as `prop.inv()`, a readable `R` bit, and an allowed cache-policy/panic condition (`ostd/src/arch/x86/mm/mod.rs:321-325`). However, `Cursor::protect_next` requires only `forall |p: PageProperty| op.requires((p,))` plus preservation of `C::tracked(...)` (`ostd/src/mm/page_table/cursor/mod.rs:3642-3655`); it does not require `op`'s result to satisfy `C::E::set_prop_req`.
- **Problem:** A legal verified caller can supply a closure whose postcondition preserves trackedness but returns a property outside `set_prop_req`. The local assumption then manufactures the missing callee precondition and allows all of `protect`'s and `protect_next`'s postconditions to be proved from an unstated caller obligation.
- **Suggestion:** Add a closure-result condition to the public `protect_next` contract (and the private `Entry::protect` contract) that implies the actual receiver's `set_prop_req` for every permitted output, and propagate/prove that condition after invoking `op`. If the intended API accepts every `PageProperty`, instead weaken/redesign the architecture-specific `set_prop_req` and prove `set_prop` for those cases. In either design, delete the `assume`.

## Medium

### `Child::Frame` conversion assumes the new architecture-specific constructor requirement

- **Guideline:** `centralize-trusted-boundaries`
- **Location:** `ostd/src/mm/page_table/node/child.rs:112`
- **Evidence:** In the `Child::Frame(paddr, level, prop)` arm, the patch adds `assume(C::E::new_page_req(paddr, level, prop));` immediately before `C::E::new_page(paddr, level, prop)`. The enclosing `into_pte` contract requires `self.invariants(...)` but does not directly require `new_page_req` (`child.rs:65-78`), while the trait now makes that predicate a hard precondition of `new_page` (`ostd/src/mm/page_table/mod.rs:527-535`). For x86, `new_page_req` includes `prop.inv()`, the `R` bit, and the cache-policy condition (`ostd/src/arch/x86/mm/mod.rs:215-219`).
- **Problem:** The generic conversion silently trusts an implementation-specific construction obligation instead of deriving it from the `Child` invariant. This is a local trusted boundary in ordinary page-table code, and it permits `into_pte` to claim its invariant-preserving postconditions even if a `Frame` value does not meet the selected architecture's constructor contract.
- **Suggestion:** Make the `Child::Frame` branch of `Child::invariants` imply `C::E::new_page_req(paddr, level, prop)`, then prove that every `Child::Frame` constructor preserves the strengthened invariant. Alternatively, define a common architecture-independent validity predicate strong enough to imply `new_page_req`. Use that fact at line 112 and remove the `assume`.

## Low

No low-severity findings.

## Evidence check record

- Read the complete authoritative 2,738-line `diff.patch`; inspected the corresponding `before/` and `after/` definitions and callers for both added assumptions.
- Confirmed that `PageTableEntryTrait::new_page` requires `Self::new_page_req(...)` and `set_prop` requires `old(self).set_prop_req(...)` in the after snapshot.
- Confirmed that the x86 predicates impose concrete conditions beyond the contracts of the generic call sites, and that `Cursor::protect_next` does not constrain the closure result with `set_prop_req`.
- Searched the changed snapshots for `assume`, `admit`, `external_body`, and `rlimit`. The two added assumptions above are the relevant new trust sites. Changed rlimits do not exceed 200 (`200` and `80` were observed), so no rlimit finding is reported.
- The patch removes the local `bit_mapping` model in favor of direct verified flag encoding; no strong duplicate-specification or missed-reuse finding was established.
- **No-verification disclosure:** Per the requested fast-review override, no Verus run, build, history analysis, caller experiment, or exhaustive guideline pass was performed. Findings are based on static contract and source evidence only.
