use vstd::prelude::*;

use crate::specs::arch::model::ArchAddressSpaceModel;

use crate::{
    arch::mm::PagingConsts,
    mm::{
        MAX_PADDR, Paddr, PagingConstsTrait, Vaddr,
        kspace::{LINEAR_MAPPING_BASE_VADDR, VMALLOC_BASE_VADDR},
    },
};

verus! {

/// The RISC-V instance of the architecture-wide specification contract.
///
/// The address constants are shared by all architectures in `mm::kspace`, so
/// the numeric requirements below follow from the shared values. Sv48 page-table
/// semantics and the linear-mapping window connection are not established here.
pub ghost struct RiscvArch;

impl ArchAddressSpaceModel for RiscvArch {
    type C = PagingConsts;

    open spec fn max_paddr_spec() -> Paddr {
        MAX_PADDR
    }

    open spec fn linear_mapping_base_vaddr_spec() -> Vaddr {
        LINEAR_MAPPING_BASE_VADDR
    }

    open spec fn vmalloc_base_vaddr_spec() -> Vaddr {
        VMALLOC_BASE_VADDR
    }

    proof fn lemma_model_requirements() {
        assert(Self::linear_mapping_base_vaddr_spec() % Self::C::BASE_PAGE_SIZE() == 0)
            by (compute_only);

        assert(Self::max_paddr_spec() + Self::linear_mapping_base_vaddr_spec()
            < Self::vmalloc_base_vaddr_spec()) by (compute_only);
    }
}

} // verus!
