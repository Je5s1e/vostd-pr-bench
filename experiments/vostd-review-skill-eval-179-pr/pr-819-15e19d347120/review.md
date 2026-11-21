# Review: PR 819 isolated snapshot `15e19d347120`

> Produced from the bundled VOSTD review skill's coding-guideline and API-contract criteria.
> Scope: authoritative `diff.patch` (957 lines), with `before/` and `after/` used only for source context and line locations.

**Bottom line:** The new public trusted models omit essential safety obligations for raw-pointer arithmetic/volatile access and privileged MSR access. That lets verification accept calls for which the underlying unsafe APIs do not promise a valid execution, so the trusted boundary should be corrected before merge. The patch also leaves several broad trusted bodies beside their APIC callers instead of isolating the unsupported primitives.

## High

### External specifications omit the unsafe APIs' validity conditions

- **Guideline:** `complete-external-contracts`
- **Locations:** `verified_libs/vstd_extra/src/external/ptr.rs:110`, `verified_libs/vstd_extra/src/external/x86.rs:55`
- **Quoted evidence:**

  ```rust
  pub assume_specification<T>[ <*mut T>::add ](ptr: *mut T, count: usize) -> (ret: *mut T)
      requires
          ptr@.addr + count * size_of::<T>() <= usize::MAX,
          count * size_of::<T>() <= isize::MAX,
  ```

  ```rust
  pub assume_specification[ x86::msr::rdmsr ](msr: u32) -> u64
      opens_invariants none
      no_unwind
  ;
  ```

  The adjacent `read_volatile`/`write_volatile` models likewise require only numeric non-overflow and alignment (`ptr.rs:113-128`). Numeric address bounds are not the safety contract of `ptr.add`: both endpoints must remain within the same allocated object (or one-past it). Volatile access also needs an address valid for that access (including the special outside-allocation I/O rules), and `rdmsr`/`wrmsr` require an MSR/privilege context in which the instruction is valid. The patch itself acknowledges the latter requirement at `ostd/src/arch/x86/kernel/apic/x2apic.rs:66-69`, while the trusted specification accepts every `u32`. These public models therefore discharge unsafe operations without representing the conditions that make the real operations valid.

  **Suggestion:** Give these models explicit validity capabilities/predicates that capture the real safety domains. Keep `ptr.add`'s same-allocation/in-bounds contract faithful; for MMIO addresses, use a separate architecture-specific trusted accessor or integer-address construction path rather than weakening generic pointer arithmetic. Similarly, restrict MSR reads/writes with a reviewed register/CPU-mode predicate (or narrow wrappers for the specific APIC registers), and require callers to establish it.

## Medium

### Broad APIC operations are trusted locally instead of isolating unsupported primitives

- **Guideline:** `centralize-trusted-boundaries`
- **Locations:** `ostd/src/arch/x86/kernel/apic/xapic.rs:46`, `ostd/src/arch/x86/kernel/apic/xapic.rs:61`, `ostd/src/arch/x86/kernel/apic/x2apic.rs:29`, `ostd/src/arch/x86/kernel/apic/x2apic.rs:49`, `ostd/src/arch/x86/kernel/apic/x2apic.rs:102`
- **Quoted evidence:**

  ```rust
  pub uninterp spec fn apic_register_file_vaddr_spec() -> usize;
  pub uninterp spec fn has_xapic_spec() -> bool;
  ...
  #[verus_verify(external_body)]
  pub fn new() -> Option<Self> { ... }
  ```

  ```rust
  /* The polling loop terminates only on hardware action; whole op unverified. */
  #[verus_verify(external_body)]
  unsafe fn send_ipi(&self, icr: super::Icr) { ... }
  ```

  The unsupported facts are CPUID, raw MMIO address construction, and hardware-driven polling, but the patch trusts whole local methods and keeps their uninterpreted models next to the callers. This makes future changes to the ordinary control flow and register sequence invisible to verification and spreads the trust boundary across both APIC implementations.

  **Suggestion:** Move the primitive CPUID/MMIO/hardware-progress models into `vstd_extra::external` (or another single reviewed boundary), expose narrow contracts, and verify the APIC constructors and register sequence against those contracts. If termination cannot be promised, isolate only the hardware wait primitive rather than marking the entire `send_ipi` implementation `external_body`.

## Low

| Finding | Guideline | Detail |
|---|---|---|
| Use the established pointer-address model | `use-addr-for-pointers` | `verified_libs/vstd_extra/src/external/ptr.rs:115-143` and `ostd/src/arch/x86/kernel/apic/xapic.rs:37-43` repeatedly use `ptr@.addr`. Replace these with `ptr.addr()` so the contracts use the same pointer-identity abstraction as the existing pointer specifications. This is a mechanical cleanup, but useful here because the new contracts make address reasoning part of a trusted boundary. |
| Propose reusable core pointer models upstream | `upstream-reusable-specs` | The new `core::ptr::{read_volatile,write_volatile}` and `<*mut T>::add` specifications at `verified_libs/vstd_extra/src/external/ptr.rs:110-145` are generic `core` API models, not OSTD-specific facts. After correcting their safety contracts, propose them to upstream Verus/vstd to avoid a second long-lived trust source. |

## Evidence check record

- Read the complete authoritative `diff.patch` and checked the cited locations in the `after/` snapshot; the corresponding `before/` files were used only to confirm that the reported trust/contracts are introduced by this patch.
- Static checks found no added or changed `#[verifier::rlimit(...)]`; therefore there is no `rlimit > 200` finding.
- The high finding was checked against the exact generic signatures and the patch's own safety statement for MSR operations. The correction deliberately separates ordinary allocated-pointer arithmetic from MMIO access rather than pretending that numeric bounds establish allocation provenance.
- No history inspection, exhaustive rule enumeration, Verus run, caller experiment, or CI verification was performed, per the requested fast-review override. The isolated snapshot does not contain the full live `docs/coding-guidelines` tree; guideline IDs and criteria were taken from the bundled `vostd-code-review` skill/personas (with the available maintainability rule text used for `use-addr-for-pointers`).

