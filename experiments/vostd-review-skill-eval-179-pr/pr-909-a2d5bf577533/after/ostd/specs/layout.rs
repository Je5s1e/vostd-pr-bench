// SPDX-License-Identifier: MPL-2.0
//! Shared integer layouts, checked for the target during code generation.
use vstd::{
    layout::{align_of, size_of},
    prelude::*,
};

verus! {

// Asterinas is designed for 64-bit architectures.
global size_of usize == 8;

global size_of isize == 8;

global layout u16 is size == 2, align == 2;

global layout u32 is size == 4, align == 4;

/// Establishes the shared integer layouts.
pub proof fn lemma_primitive_layout()
    ensures
        size_of::<u16>() == 2,
        align_of::<u16>() == 2,
        size_of::<u32>() == 4,
        align_of::<u32>() == 4,
        core::mem::size_of::<u16>() == 2,
        core::mem::size_of::<u32>() == 4,
{
    broadcast use {VERUS_layout_of_u16, VERUS_layout_of_u32};

}

} // verus!
