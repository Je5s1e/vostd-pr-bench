# Review: PR 92 captured patch

> Produced from the authoritative `diff.patch` and the captured before/after source context. Scope: the three changed files under `lock-protocol/src/mm/page_table/` in `pr-92-8fe6908fea09`.

**Bottom line:** The new `from_raw_paddr` postcondition claims a bounded physical address for every possible input, although the API has no corresponding precondition. This either makes a conforming implementation impossible to verify for out-of-range inputs or, if an implementation is trusted, exposes an unjustified fact to every caller. No other strong, evidence-backed issue was found in the captured patch.

## High

None.

## Medium

### `from_raw_paddr` promises well-formedness for arbitrary addresses

- **Guideline:** `api-preconditions`
- **Location:** `lock-protocol/src/mm/page_table/node/mod.rs:134`
- **Evidence:** The newly added predicate is `self.paddr() < exec::PHYSICAL_BASE_ADDRESS_SPEC() + exec::SIZEOF_FRAME * exec::MAX_FRAME_NUM` (lines 47–51), while `fn from_raw_paddr(paddr: Paddr)` has no `requires` clause and now ensures both `res.paddr() == paddr` and `res.wf()` (lines 134–138).
- **Problem:** For an input at or above the stated bound, the two postconditions imply both that the result's address equals that input and that the same address is below the bound. The contract therefore grants callers a false range fact for an unrestricted input; a verified implementation cannot establish it, while a trusted implementation would turn it into an unsound assumption.
- **Suggestion:** Add the address-bound requirement to `from_raw_paddr` (preferably via a precisely named reusable predicate), and prove it at each call site before constructing the lock. If the runtime constructor intentionally accepts arbitrary raw addresses, remove `res.wf()` and establish `wf()` only after validation.

## Low

None.

## Evidence check record

- Read the authoritative patch in full and compared the changed declarations and their surrounding source in the captured before/after trees.
- Traced all captured `PTL::from_raw_paddr` call sites and checked the definition of the newly added `wf` predicate. The signature itself has no input restriction that could refute the finding.
- Checked the patch for changed `#[verifier::rlimit(...)]` attributes and new or materially changed external specifications for `std`, `core`, or `alloc`; none are present.
- The `path_wf` refactoring was compared with its prior formula. The new adjacent-node `points_to` relation uses `level_at_path_index(j) = j + 1`, matching the former PTE level for adjacent indices, so no contract regression was reported there.
- Per the fast-review constraint, no Verus run, build, history analysis, exhaustive guideline pass, or isolated caller experiment was performed. Findings are based on static source and contract evidence only.
