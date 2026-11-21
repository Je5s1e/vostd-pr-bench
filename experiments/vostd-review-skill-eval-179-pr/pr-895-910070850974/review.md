# Review: PR 895 snapshot (`diff.patch`)

> Fast isolated VOSTD review using `diff.patch` as the authoritative change and the supplied `before/` and `after/` trees as context.
> Scope: maintainability, proof/trust assumptions, API contracts and invariants, specification reuse, and the workflow checks for `rlimit > 200` and upstreamable external specifications.

**Bottom line:** This change is not merge-ready because it obtains a small verified surface by disabling most of the existing PCI subsystem. Bus initialization, PCI enumeration, configuration-space access, BAR I/O, MSI-X support, vendor-capability access, and public PCI modules are placed inside block comments or removed from the module surface. Restore the executable implementation and verify it incrementally without changing or suppressing the runtime path.

## High

### The verification patch disables the PCI runtime implementation

- **Guideline:** `preserve-exec-code`
- **Locations:** `ostd/src/bus/mod.rs:14`, `ostd/src/bus/pci/mod.rs:51`, `ostd/src/bus/pci/cfg_space.rs:346`, `ostd/src/bus/pci/capability/msix.rs:6`, `ostd/src/bus/pci/capability/vendor.rs:19`, `ostd/src/bus/pci/device_info.rs:30`
- **Quoted evidence:** The patch changes `pub mod bus;` and `pub mod common_device;` to `/*pub mod bus;*/` and `/*pub mod common_device;*/`; wraps `pub(crate) fn init() { pci::init(); }` in `/* ... */`; and encloses the implementations of `IoBar::read`/`write`, `CapabilityVndrData::read*`/`write*`, MSI-X support, device discovery, and PCI configuration-space access in block comments. At the same time, the newly active verified code is limited to leaf items such as `#[verus_spec(returns self.base())]`, `#[verus_spec(returns self.len())]`, and the private `set_bit` helper.
- **Problem:** This is a functional deletion, not a proof-only refactoring. The resulting module no longer initializes or enumerates PCI devices and removes previously public PCI APIs merely to shrink the code accepted by verification; commenting the old source in place does not preserve its executable behavior or API availability.
- **Suggestion:** Remove the block-comment scaffolding, restore the original module declarations, bus initialization, constructors, and I/O/capability implementations, and introduce verification annotations in small behavior-preserving steps. If a specific original operation is not yet supported by Verus, isolate and document that precise boundary rather than disabling unrelated callers and runtime functionality.

## Medium

None.

## Low

None.

## Evidence check record

- Read the complete 293-line authoritative `diff.patch` and inspected the corresponding `before/` and `after/` source around every changed hunk.
- Confirmed statically that the disabled code includes active module exports and executable initialization, discovery, configuration-space, BAR, MSI-X, and vendor-capability paths; these are not ghost/proof-only items.
- Searched the snapshot for `#[verifier::rlimit(...)]`, trusted assumptions/external bodies, and newly added external specifications. The patch contains no changed rlimit, no new trusted assumption or external body, and no new `std`/`core`/`alloc` external specification, so neither narrow workflow check is triggered.
- Searched the supplied verified-code snapshot for an existing equivalent `set_bit` specification and found no evidence strong enough for a specification-reuse finding.
- No separate API-precondition, API-postcondition, invariant, or trust-boundary finding survived static review; the exact getter/constructor results and the `offset < 16` non-panicking bound are consistent with the visible implementations.
- **No-verification disclosure:** Per the fast-review scope, no Verus run, Cargo/build/test run, caller experiment, repository-history analysis, or exhaustive guideline-rule audit was performed. Conclusions are based only on the authoritative patch and supplied before/after context.
