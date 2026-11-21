//! Architecture selection and shared memory specifications.
//!
//! # Verified Properties
//!
//! [`CurrentArch`] selects the target's implementation of the contracts in [`model`].
//! The erased [`valid_frame_paddr`] predicate requires base-page alignment and an
//! address below that implementation's modeled physical-memory bound. Shared
//! constants are re-exported from the executable architecture and memory modules.
//! The model's conversion lemma establishes bounds within the linear mapping window.
use vstd::prelude::*;

use crate::specs::arch::model::{lemma_paddr_to_vaddr_properties_for, valid_frame_paddr_for};

use crate::mm::{
    Paddr,
    kspace::{LINEAR_MAPPING_BASE_VADDR, VMALLOC_BASE_VADDR, paddr_to_vaddr},
};

pub mod model;

pub use model::ArchAddressSpaceModel;

// Compatibility re-exports for proof modules that still use `specs::arch`.
// The authoritative values live in the executable memory/architecture modules.
pub use crate::{
    arch::mm::{NR_ENTRIES, NR_LEVELS, PAGE_SIZE},
    mm::{MAX_NR_PAGES, MAX_PADDR},
};

#[cfg(target_arch = "x86_64")]
mod x86;
/// The architecture selected by the current verification target.
#[cfg(target_arch = "x86_64")]
pub use x86::X86Arch as CurrentArch;

#[cfg(target_arch = "riscv64")]
mod riscv;
/// The architecture selected by the current verification target.
#[cfg(target_arch = "riscv64")]
pub use riscv::RiscvArch as CurrentArch;

#[cfg(target_arch = "loongarch64")]
mod loongarch;
/// The architecture selected by the current verification target.
#[cfg(target_arch = "loongarch64")]
pub use loongarch::LoongArch as CurrentArch;

verus! {

/// A physical address that can identify a base-page frame on the selected architecture.
pub open spec fn valid_frame_paddr(paddr: Paddr) -> bool {
    valid_frame_paddr_for::<CurrentArch>(paddr)
}

/// Relates the current linear mapping to its architecture model.
pub proof fn lemma_paddr_to_vaddr_properties(pa: Paddr)
    requires
        pa < VMALLOC_BASE_VADDR - LINEAR_MAPPING_BASE_VADDR,
    ensures
        paddr_to_vaddr(pa) == model::paddr_to_vaddr_for::<CurrentArch>(pa),
        LINEAR_MAPPING_BASE_VADDR <= paddr_to_vaddr(pa) < VMALLOC_BASE_VADDR,
{
    lemma_paddr_to_vaddr_properties_for::<CurrentArch>(pa);
}

pub proof fn lemma_max_paddr_range()
    ensures
        MAX_PADDR < VMALLOC_BASE_VADDR - LINEAR_MAPPING_BASE_VADDR,
        MAX_PADDR + LINEAR_MAPPING_BASE_VADDR < usize::MAX,
{
    CurrentArch::lemma_model_requirements();
}

} // verus!
