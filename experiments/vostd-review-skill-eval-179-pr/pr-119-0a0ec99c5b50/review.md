# Review: PR 119 `618a49450d5d73ed3a590dd24e918929c14ac32a..0a0ec99c5b505bd7511d73e9ac4572bd96c22311`

> Fast static review of `diff.patch` against the VOSTD API-contract criteria and the requested trust-boundary checks. No Verus or other verification was run.
> Scope: `diff 618a49450d5d73ed3a590dd24e918929c14ac32a..0a0ec99c5b505bd7511d73e9ac4572bd96c22311`; authoritative changed path: `lock-protocol/src/mm/page_table/node/entry.rs`.

**Bottom line:** The patch replaces the old frame condition with a more precise one, but supplies the address from the post-state `self.pte`. This function has already replaced that PTE with `Child::None`, so the exception does not identify the old entry being removed. The body then `assume`s the same mismatched predicate, creating a proof trust hole and making the advertised postcondition unreliable.

## High

### The frame condition exempts the post-state PTE instead of the removed PTE

- **Guideline:** `api-postconditions` (with a proof/trust-boundary violation at the corresponding `assume`)
- **Location:** `lock-protocol/src/mm/page_table/node/entry.rs:246` and `lock-protocol/src/mm/page_table/node/entry.rs:299`
- **Quoted evidence:** The new postcondition is `spt_do_not_change_except(spt, old(spt), self.pte.pte_paddr() as int)`, and the body repeats it as `assume(spt_do_not_change_except(spt, old(spt), self.pte.pte_paddr() as int));`. Nearby code constrains `new_child` to `Child::None` (lines 236–239) and then executes `self.pte = new_child.into_pte();` (line 263), while the removed address is consistently referenced as `old(self).pte.pte_paddr()` at lines 235, 243, and 297.
- **Problem:** In an `ensures` clause, `self.pte` is the post-state field. The only entry allowed to change should be the old PTE being removed, but the new predicate instead exempts the replacement PTE. Because the implementation assumes this mismatched statement rather than deriving it, verification could accept a false frame condition and callers cannot rely on the API's claimed preservation property.
- **Suggestion:** Use `old(self).pte.pte_paddr() as int` as the exception address in both the postcondition and the proof statement, and prove the frame condition instead of assuming it (or retain an assumption only with an explicit, sound justification at the trust boundary).

## Medium

No findings.

## Low

No findings.

## Evidence check record

- Reviewed all 26 lines of `diff.patch`; it changes only the frame-condition expression in `replace_with_none` and the matching `assume`.
- Checked nearby after-state source at lines 223–301: the precondition forces `new_child` to `Child::None`, line 263 overwrites `self.pte`, and the removal assertions use `old(self).pte.pte_paddr()`.
- Checked `spt_do_not_change_except` in `cursor/spec_helpers.rs:43–86`: its `pte_addr` argument is the sole exception used by the quantified preservation conditions for PTE maps and ancestor chains, so selecting the wrong address materially changes the contract.
- No executable Rust was changed, no `#[verifier::external_body]`, `admit`, or rlimit was added or modified, and no newly changed `std`/`core`/`alloc` external specification was present in scope.
- This was a fast, non-exhaustive static review. No history fetch, isolated caller experiment, Verus run, or CI verification was performed.
