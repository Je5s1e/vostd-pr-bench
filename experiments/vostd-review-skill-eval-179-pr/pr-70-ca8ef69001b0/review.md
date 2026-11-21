# Review: PR 70 (`ca8ef69001b0`)

> Fast isolated VOSTD review using `diff.patch` as the authoritative change and the supplied `before/` and `after/` files as context.
> Scope: `lock-protocol/src/exec/rw/pte/page_table_entry.rs` and `lock-protocol/src/exec/rw/pte/page_table_entry_trait.rs`.

**Bottom line:** The new physical-address mask is incompatible with the accepted input domain and with the trusted trait property. A concrete, newly affected address is accepted by `valid_paddr`, truncated by both constructors, and nevertheless asserted by an `external_body` lemma to round-trip unchanged. This is a proof-soundness blocker until the valid-address invariant and constructor contracts agree with the mask.

## High

### The trusted PTE property is false for inputs newly truncated by the mask

- **Guidelines:** `complete-external-contracts`, `centralize-trusted-boundaries`, `api-preconditions`, `api-postconditions`
- **Locations:** `lock-protocol/src/exec/rw/pte/page_table_entry.rs:33`, `lock-protocol/src/exec/rw/pte/page_table_entry.rs:60`, `lock-protocol/src/exec/rw/pte/page_table_entry.rs:90`, `lock-protocol/src/exec/rw/pte/page_table_entry.rs:242`, `lock-protocol/src/exec/rw/pte/page_table_entry_trait.rs:130`
- **Evidence:** The PR changes the mask to `returns 0xF_FFFF_FFFF_F000 as usize`. Both `new_page_spec` and `new_pt_spec` store `paddr & Self::PHYS_ADDR_MASK()`. In the supplied context, `valid_paddr(pa)` is still defined as `true`. Nevertheless, the trait lemma promises for every valid `p` that `Self::new_page(p, ...).paddr_spec() == p` and `Self::new_pt(p).paddr_spec() == p`, and the implementation discharges that lemma with an empty `#[verifier::external_body]`.
- **Problem:** Let `p = 1usize << 52`. It is page-aligned and satisfies the current `valid_paddr`, but `p & 0xF_FFFF_FFFF_F000 == 0`; therefore either constructor's `paddr_spec()` is `0`, contradicting the trusted claim that it equals `p`. Bit 52 was retained by the old `0x7fff_ffff_ffff_f000` mask, so this witness is introduced by the reviewed mask change. Removing the direct address postconditions from `new_page` and `new_pt` does not repair the model because the stronger false claim remains available through the trusted lemma.
- **Suggestion:** Define the valid physical-address domain to include the actual architectural range and page-alignment requirements (in particular, require `paddr & !PageTableEntry::PHYS_ADDR_MASK() == 0` and the appropriate low-bit alignment), then restore an exact abstract constructor guarantee such as `res.paddr_spec() == paddr` for valid inputs. Prove `lemma_page_table_entry_properties` from those definitions instead of admitting it with `external_body`; if truncation is intentionally part of the API, document and specify the masked result consistently and remove the contradictory exact-round-trip lemma.

## Medium

No findings.

## Low

No findings.

## Evidence check record

- Read all 568 lines of `diff.patch`; used the supplied before/after versions of both changed files plus `common.rs` as contextual evidence.
- Refutation check: the exact witness `1usize << 52` is accepted because `valid_paddr` is literally `true`, is cleared by the new 52-bit mask, and therefore cannot satisfy the trusted equality. The constructor flags occupy non-address bits, so they do not restore bit 52.
- The two removed direct postconditions and the unchanged trusted lemma were checked together; they represent one root cause and are consolidated above.
- No `#[verifier::rlimit(...)]` change and no new or materially changed `std`/`core`/`alloc` external specification appears in the authoritative diff.
- No Verus run, history analysis, caller experiment, or exhaustive guideline pass was performed, per the fast-review override. Findings are based on static inspection only.
