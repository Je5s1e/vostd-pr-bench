# Review: `diff.patch` before/after scope (PR 865 snapshot)

> Produced from the VOSTD coding-guideline review criteria and the skill's API-contract criteria.
> Scope: the complete `diff.patch`, with `before/` and `after/` used only for surrounding source context.

**Bottom line:** The patch blocks LoongArch from compiling: it comments out most of the architecture module declarations and all of the architecture entry points while shared code still calls those items on LoongArch. Restore this executable architecture surface before merging; the verification additions can remain scoped to the page-table code without deleting unrelated runtime code.

## High

### The patch removes the LoongArch runtime architecture surface

- **Guideline:** `preserve-exec-code`
- **Location:** `ostd/src/arch/loongarch/mod.rs:3`
- **Evidence:** The before version declares `pub mod boot;`, `pub(crate) mod cpu;`, `pub mod device;`, `pub(crate) mod iommu;`, `pub mod kernel;`, `pub(crate) mod pci;`, `pub mod qemu;`, `pub(crate) mod serial;`, `pub(crate) mod task;`, and `pub mod trap;`, and defines `late_init_on_bsp`, `init_on_ap`, `interrupts_ack`, `tsc_freq`, `read_tsc`, `read_random`, and `enable_cpu_features`. The after version wraps those declarations and every one of those functions in block comments (`ostd/src/arch/loongarch/mod.rs:3-7`, `:9`, `:11-14`, and `:16-69`). These are not dead declarations: shared source still calls `arch::enable_cpu_features()` and `arch::late_init_on_bsp()` (`ostd/src/lib.rs:87,124`), imports/calls `arch::serial` (`ostd/src/lib.rs:96-99`), calls `crate::arch::trap::init()` and `crate::arch::init_on_ap()` (`ostd/src/boot/smp.rs:133,137`), and calls `crate::arch::interrupts_ack(...)` (`ostd/src/trap/handler.rs:66`).
- **Problem:** On a LoongArch build those selected architecture items no longer exist, so name resolution fails before any of the new page-table verification can be used. The change also removes boot, CPU-local, trap, task, serial, PCI, and initialization behavior from the executable architecture merely by commenting it out.
- **Suggestion:** Restore the original module declarations and architecture entry-point implementations unchanged. If individual modules cannot yet pass the verification frontend, exclude or annotate only the minimum verification boundary needed, while preserving the original executable Rust and recording any required rewrite with the mandated `Origin Rust:` form.

## Medium

No evidence-backed medium-severity findings.

## Low

No useful low-severity findings.

## Evidence check record

- Read `diff.patch` in full scope and compared the affected LoongArch module against both `before/` and `after/` context.
- Refutation check: searched the after tree for consumers of the removed modules and entry points. The cited shared call sites remain active and are not guarded away from `target_arch = "loongarch64"`.
- Contract/proof review included the changed `PageTableEntryTrait::set_prop` contract, architecture-specific `set_prop_ensures` predicates, LoongArch page-table preconditions and postconditions, the added trusted hardware-reader boundary, and the changed kernel-range facts. No additional high/medium finding was retained without stronger caller-impact evidence.
- No `#[verifier::rlimit(...)]` change appears in the patch, so the `rlimit > 200` workflow check was not triggered.
- No newly added or materially changed external specification for a `std`, `core`, or `alloc` API appears in the patch, so the upstream-spec workflow check was not triggered.
- **No-verification disclosure:** Per the requested fast-review override, I did not run Verus, compile the LoongArch target, execute caller experiments, inspect repository history, delegate persona passes, or perform the exhaustive guideline checklist. The blocking result above is based on direct before/after source and unresolved-call-site evidence.
