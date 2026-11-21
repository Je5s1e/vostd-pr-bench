# Review: PR 847 snapshot `diff.patch`

> Fast, non-exhaustive VOSTD review of the supplied before/after snapshot and `diff.patch` only.
> Scope: the 15 paths changed by `pr-847-deb42343023f/diff.patch`; no repository history, Verus run, exhaustive guideline checklist, or caller experiment was performed.

**Bottom line:** The patch enables the RISC-V architecture at the crate root while simultaneously block-commenting most of that architecture's module surface and runtime implementation. That is a blocking executable regression and obscures the actual verification boundary. The new trusted model for reading `satp` also represents mutable hardware state as a single fixed spec value, so it cannot soundly describe reads across page-table activation or other hardware transitions.

## High

### RISC-V is exposed after most of its executable architecture support is removed

- **Guideline:** `preserve-exec-code`
- **Location:** `ostd/src/arch/riscv/mod.rs:3` (also `ostd/src/arch/riscv/timer/mod.rs:4`)
- **Evidence:** The before snapshot exports `boot`, `cpu`, `device`, `iommu`, `pci`, `qemu`, `serial`, `task`, and `trap`; the after snapshot replaces those declarations with `/*pub mod boot; ... */` and wraps every architecture entry point from `init_cvm_guest` through `enable_cpu_features` in another block comment. The timer implementation is likewise wrapped from its `core` imports through `get_timebase_freq`, leaving only `TIMER_FREQ`. In the same patch, `ostd/src/lib.rs:37-39` newly enables this reduced module as `pub mod arch` under `target_arch = "riscv64"`.
- **Problem:** This is not a proof-only rearrangement: it removes the runtime RISC-V architecture API and initialization/timer behavior from compilation precisely when the crate begins selecting that architecture. Existing source still refers to architecture facilities such as `crate::arch::boot`, `crate::arch::cpu`, `crate::arch::task`, and `crate::arch::trap`; hiding the declarations behind comments makes the verification subset diverge from the executable program and makes downstream integration fail or silently omit required behavior depending on which surrounding modules remain enabled.
- **Suggestion:** Restore the executable module declarations and bodies byte-for-byte, then isolate verification with supported per-item annotations, specifications, or narrowly scoped configuration that does not change the production module graph. If a target cannot yet be verified, exclude that verification target explicitly and document the concrete blocker rather than commenting out runtime code.

## Medium

### The `satp` reader models changing hardware state as one immutable value

- **Guidelines:** `complete-external-contracts`, `centralize-trusted-boundaries`
- **Location:** `ostd/src/arch/riscv/mm/mod.rs:252`
- **Evidence:** The patch adds `pub uninterp spec fn current_page_table_paddr_spec() -> Paddr;` and gives the external body `current_page_table_paddr()` the exact result contract `returns current_page_table_paddr_spec()`. Immediately above it, `activate_page_table` writes `satp`, while the added comment concedes: `The hardware read is trusted; the contract does not model satp transitions.` The reader is used by page-table and VM-space code, including equality checks against a root page-table address.
- **Problem:** A zero-argument uninterpreted function denotes one fixed mathematical value, so every verified read is specified to return the same address even though `satp` can change through `activate_page_table`, interrupts, or other trusted hardware actions. The contract therefore supplies a stronger stability fact than the hardware API supports; acknowledging the omission in a comment does not constrain proofs. Keeping the `external_body` and hardware model beside the caller-facing architecture implementation also spreads the trust boundary instead of placing it in the external-spec layer.
- **Suggestion:** Model the active page table as explicit state (for example, a tracked/ghost machine-state token whose transition is specified by activation), or give reads a deliberately nondeterministic result plus only stable facts that each read really guarantees, such as required alignment/range. Move the minimal hardware assumption into the centralized external-spec layer and connect both read and write operations to the same model; do not expose cross-call equality without a state-stability premise.

## Low

No strong low-severity findings.

## Evidence check record

- Read the complete supplied `diff.patch` scope and inspected the corresponding before/after files for both findings.
- Confirmed the RISC-V module declarations and runtime bodies are present before the patch and block-commented afterward; confirmed the crate root newly selects the RISC-V module.
- Searched the after snapshot for references to the removed architecture modules and for callers of `current_page_table_paddr`; both remain in the source tree.
- Confirmed there are no added or changed `#[verifier::rlimit(...)]` attributes, so the `> 200` workflow check did not trigger.
- No materially changed external specification for a `std`, `core`, or `alloc` API was found in the diff, so the upstream-spec-reuse workflow check did not trigger.
- The new RISC-V `current_page_table_paddr_spec` mirrors an existing x86-local pattern, but that does not make its fixed-value model valid for mutable hardware state and reinforces the need for one shared external boundary rather than another architecture-local trust source.
- **No-verification disclosure:** Per the requested fast-review constraints, no Verus invocation, build, test, isolated client experiment, history inspection, or exhaustive guideline pass was performed. Findings are based on static before/after and call-site evidence only.
