#![allow(non_snake_case)]
#[allow(unused_parens)]
#[allow(unused_braces)]
#[allow(rustdoc::invalid_rust_codeblocks)]
#[allow(rustdoc::invalid_html_tags)]
pub mod arch;
#[allow(unused_parens)]
#[allow(unused_braces)]
#[allow(rustdoc::invalid_rust_codeblocks)]
#[allow(rustdoc::invalid_html_tags)]
pub mod mm;
#[allow(unused_parens)]
#[allow(unused_braces)]
mod sync;
#[allow(unused_parens)]
#[allow(unused_braces)]
pub mod task;

vstd::prelude::verus! {

// Asterinas is designed for 64-bit architectures.
// Verus checks these sizes against the target layout during compilation.
global size_of usize == 8;

global size_of isize == 8;

} // verus!
