//! Literal mirrors of the [`x86` crate](https://crates.io/crates/x86) (0.52.0)
//! constants, which verified code cannot reference across the crate boundary;
//! values are trusted byte-for-byte with the crate sources. Also models the
//! [`x86_64` crate](https://crates.io/crates/x86_64) (0.14.13) MSR accessors.
use vstd::prelude::*;

use x86_64::registers::model_specific::Msr;

verus! {

pub const XAPIC_ID: u32 = 0x020;

pub const XAPIC_VERSION: u32 = 0x030;

pub const XAPIC_EOI: u32 = 0x0B0;

pub const XAPIC_SVR: u32 = 0x0F0;

pub const XAPIC_ESR: u32 = 0x280;

pub const XAPIC_ICR0: u32 = 0x300;

pub const XAPIC_ICR1: u32 = 0x310;

pub const XAPIC_LVT_TIMER: u32 = 0x320;

pub const XAPIC_TIMER_INIT_COUNT: u32 = 0x380;

pub const XAPIC_TIMER_CURRENT_COUNT: u32 = 0x390;

pub const XAPIC_TIMER_DIV_CONF: u32 = 0x3E0;

pub const IA32_APIC_BASE: u32 = 0x1b;

pub const IA32_X2APIC_APICID: u32 = 0x802;

pub const IA32_X2APIC_VERSION: u32 = 0x803;

pub const IA32_X2APIC_EOI: u32 = 0x80b;

pub const IA32_X2APIC_SIVR: u32 = 0x80f;

pub const IA32_X2APIC_ESR: u32 = 0x828;

pub const IA32_X2APIC_ICR: u32 = 0x830;

pub const IA32_X2APIC_LVT_TIMER: u32 = 0x832;

pub const IA32_X2APIC_INIT_COUNT: u32 = 0x838;

pub const IA32_X2APIC_CUR_COUNT: u32 = 0x839;

pub const IA32_X2APIC_DIV_CONF: u32 = 0x83e;

/// [x86::msr::rdmsr](https://docs.rs/x86/0.52.0/x86/msr/fn.rdmsr.html) returns an unconstrained value.
pub assume_specification[ x86::msr::rdmsr ](msr: u32) -> u64
    opens_invariants none
    no_unwind
;

/// [x86::msr::wrmsr](https://docs.rs/x86/0.52.0/x86/msr/fn.wrmsr.html).
pub assume_specification[ x86::msr::wrmsr ](msr: u32, value: u64)
    opens_invariants none
    no_unwind
;

/// Opaque external wrapper for the x86_64 crate's MSR handle.
#[verifier::external_type_specification]
#[verifier::external_body]
pub struct ExMsr(Msr);

/// [`Msr::new`](https://docs.rs/x86_64/0.14.13/x86_64/registers/model_specific/struct.Msr.html#method.new).
pub assume_specification[ Msr::new ](reg: u32) -> Msr
    opens_invariants none
    no_unwind
;

/// [`Msr::read`](https://docs.rs/x86_64/0.14.13/x86_64/registers/model_specific/struct.Msr.html#method.read)
/// returns an unconstrained value.
pub assume_specification[ Msr::read ](msr: &Msr) -> u64
    opens_invariants none
    no_unwind
;

/// [`Msr::write`](https://docs.rs/x86_64/0.14.13/x86_64/registers/model_specific/struct.Msr.html#method.write).
pub assume_specification[ Msr::write ](msr: &mut Msr, value: u64)
    opens_invariants none
    no_unwind
;

} // verus!
