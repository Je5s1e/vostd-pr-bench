# Review: PR 820 artifact `diff.patch`

> Produced from the VOSTD review skill's API-contract criteria and a focused static review of the supplied before/after context.
> Scope: `pr-820-23c7625612f0/diff.patch` is authoritative; reviewed changes in `ostd/specs/arch/x86/irq.rs`, `ostd/specs/arch/x86/mod.rs`, and `ostd/src/arch/x86/kernel/irq/mod.rs`.

**Bottom line:** The executable mapping calculation is accompanied by a local proof, but the newly verified public method has no formal postcondition exposing the documented first-override-or-identity result. Consequently, verified callers cannot use the main property this change claims to establish. No high-severity issue was found in the supplied scope.

## High

No findings.

## Medium

### The verified mapping property is not part of the API contract

- **Guideline:** `api-postconditions`
- **Location:** `ostd/src/arch/x86/kernel/irq/mod.rs:117`
- **Evidence:** The new rustdoc promises, “The GSI calculation selects the first override for `isa_index`, or uses its identity mapping if none exists,” and `map_isa_pin_to` is newly annotated `#[verus_verify]`. However, its signature at lines 122–126 has no `ensures`/`returns` clause. The proof at lines 140–160 only concludes local assertions such as `assert(isa_mapping_correct(isa_overrides_view(overrides), isa_index, gsi_index));` before returning `self.map_gsi_pin_to(irq_line, gsi_index)`.
- **Problem:** A local assertion is discarded at the function boundary. The callable contract therefore exposes neither the selected GSI nor its relationship to the first matching override, so a verified caller cannot rely on the documented property.
- **Suggestion:** Introduce a caller-visible abstract view/predicate for the selected GSI (and, if necessary, a view of a successful `MappedIrqLine`), then add a postcondition connecting every successful result to `isa_mapping_correct(self.overrides@, isa_index, selected_gsi)`. Supply the corresponding contract/verification for the `map_gsi_pin_to` handoff, or factor the GSI calculation into a verified helper with an exact result contract and call that helper here.

## Low

No findings.

## Evidence check record

- **Static contract check:** Confirmed from the after-context that `map_isa_pin_to` has no formal postcondition, while its new rustdoc and body explicitly state and prove the first-match/identity property. Existing callers in `ostd/src/arch/x86/timer/pit.rs:190` and `ostd/src/arch/x86/timer/hpet.rs:95` do not refute the missing callable guarantee.
- **Proof/trust and assumptions:** The diff explicitly limits the MADT argument to entries returned by the iterator (`ostd/src/arch/x86/kernel/irq/mod.rs:248-255`) and does not claim to verify ACPI memory decoding. No added `assume`, `admit`, `external_body`, axiom, or other new trusted fact appears in the authoritative patch.
- **Invariants and model:** The loop invariant relates the executable override vector to the collected decoded entries, and the post-loop assertion accounts for the empty-list PIT fallback. Static inspection found no strong, independently reportable invariant defect.
- **Maintainability:** No strong maintainability defect meeting this fast review's reporting threshold was found.
- **Workflow:** The authoritative patch contains no `#[verifier::rlimit(...)]` change, so there is no `rlimit > 200` finding. It adds no external specification for a `std`, `core`, or `alloc` API.
- **Specification reuse:** The added models are IRQ/MADT-specific. Focused static inspection found no concrete equivalent definition or lemma that could support an evidence-backed reuse finding.
- **Verification disclosure:** Per the fast-review override, no Verus run, build, tests, history analysis, exhaustive rule enumeration, caller experiment, or other dynamic verification was performed. Conclusions are based only on `diff.patch` and the supplied before/after source context.
