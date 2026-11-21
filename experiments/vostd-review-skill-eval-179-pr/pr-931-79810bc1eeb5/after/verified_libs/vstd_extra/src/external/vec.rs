// SPDX-License-Identifier: MPL-2.0
use alloc::vec::Vec;
use core::{
    alloc::Allocator,
    ops::{Index, IndexMut},
    slice::SliceIndex,
};
use vstd::prelude::*;

verus! {

/// Rust 1.99.1, library/alloc/src/vec/mod.rs: IndexMut delegates through
/// DerefMut/as_mut_slice to slice indexing. This adds the missing mutation/frame
/// guarantee to vstd's inherited index_req, including for range indices.
pub assume_specification<T, I: SliceIndex<[T]>, A: Allocator>[ <Vec<T, A> as IndexMut<
    I,
>>::index_mut ](vec: &mut Vec<T, A>, index: I) -> (output: &mut <Vec<T, A> as Index<I>>::Output)
    ensures
        exists|slice: &mut [T]| #[trigger]
            slice@ == old(vec)@ && final(slice)@ == final(vec)@ && call_ensures(
                <I as SliceIndex<[T]>>::index_mut,
                (index, slice),
                output,
            ),
;

} // verus!
