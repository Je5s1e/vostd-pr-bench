# Review: PR 69 snapshot (`diff.patch`)

> Produced from the VOSTD review skill's maintainability, proof-engineering, workflow, and API-contract criteria.
> Scope: fast, non-exhaustive review of `diff.patch`, with complete captured before/after context for `lock-protocol/src/exec/rw/pte/page_table_entry.rs` and `lock-protocol/src/spec/common.rs`.

**Bottom line:** The change removes a local trust boundary from `new_pt`, but it also rewrites the executable implementation solely while adding its proof and does not preserve or explain the original executable form. Restore the original runtime expression shape, or retain the required adjacent `Origin Rust:` record and concrete Verus-related reason. No contract, invariant, rlimit, trigger, or specification-reuse defect was strong enough to report from the supplied snapshot.

## High

None.

## Medium

### Preserve the original executable construction in `new_pt`

- **Guideline:** `preserve-exec-code`
- **Location:** `lock-protocol/src/exec/rw/pte/page_table_entry.rs:359`
- **Evidence:** Before, the executable body computed `let addr = paddr & PHYS_ADDR_MASK();` and returned `Self(addr | PageTableFlags::PRESENT().bits() | PageTableFlags::WRITABLE().bits() | PageTableFlags::USER().bits())`. After, it computes `let flags = PageTableFlags::PRESENT().bits() | PageTableFlags::WRITABLE().bits() | PageTableFlags::USER().bits();` and returns `Self(paddr & PHYS_ADDR_MASK() | flags)` (lines 361 and 371), with no adjacent `Origin Rust:` block or explanation.
- **Problem:** The runtime computation is equivalently regrouped as part of proof work, even though the VOSTD rule requires specifications and proofs to be added without rewriting executable Rust; when Verus requires such a rewrite, the original form and concrete reason must remain adjacent. This obscures whether the runtime edit is necessary and makes later comparison with the upstream executable implementation harder.
- **Suggestion:** Prefer restoring the original `addr` local and original return expression, and prove the required facts using proof-only locals/assertions. If Verus genuinely requires the regrouping, keep the change minimal and add the guideline-required adjacent `Origin Rust:` block containing the original code plus the concrete reason.

## Low

None.

## Evidence check record

- Read all 53 lines of `diff.patch` and the complete captured before/after versions of both changed files (651/658 lines for `page_table_entry.rs`, 331/333 lines for `common.rs`).
- Compared the changed `new_pt_spec` and `new_pt` definitions with the surrounding PTE constructors and address/flag models. The implementation's inherited trait declaration is not included in this snapshot, so no standalone API-contract claim was made from an unseen declaration.
- The added `#[trigger] new_path.contains(n)` is attached to the quantified predicate already used by the proof; the supplied static evidence does not establish a trigger or invariant regression.
- The diff adds no `#[verifier::rlimit(...)]` and no external specification for a `std`, `core`, or `alloc` API, so neither narrow workflow check is triggered.
- The change removes `#[verifier::external_body]` from `new_pt`; no new `assume`, `admit`, axiom, uninterpreted model, or trusted body appears in scope.
- **No-verification disclosure:** Per the requested fast-review mode, no Verus run, build, tests, history inspection, isolated caller experiment, or exhaustive guideline checklist was performed. The expected top-level `docs/coding-guidelines` pages are also absent from this snapshot workspace; the finding uses the rule text available in the review skill/context and the captured source evidence.
