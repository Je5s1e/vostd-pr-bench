# Review: PR 738 isolated snapshot (`diff.patch`)

> Produced from the supplied before/after snapshot and `diff.patch`, using the VOSTD maintainability, proof-engineering, and API-contract criteria.
> Scope: fast, non-exhaustive review of the four files changed by `diff.patch`; surrounding before/after source was read for context.

**Bottom line:** The new `RwArc::as_ptr` path is backed by an `RwLock::as_ptr` implementation that casts the address of the `PCell<T>` wrapper to `*mut T` instead of obtaining the address of the value stored in the cell. This is a public raw-pointer API, so relying on the wrapper's unspecified Rust layout is merge-blocking. The API also has no formal postcondition tying its result to the protected value, making its documented purpose unavailable to verified callers.

## High

### The returned pointer is derived from the `PCell` wrapper, not its stored value

- **Guideline:** `preserve-exec-code`
- **Location:** `ostd/src/sync/rwlock.rs:636` (exposed through `ostd/src/sync/rwarc.rs:80-82`)
- **Evidence:** The new trusted implementation is `core::ptr::from_ref(&self.val) as *const T as *mut T`. Here `self.val` has type `PCell<T>` (`rwlock.rs:171`), while the same file documents the actual cell access as `unsafe { &(*(*self.ucell).get()) }` at `rwlock.rs:740-743`. The public method then returns this value unchanged: `pub fn as_ptr(&self) -> *const T { self.0.data.as_ptr() }`.
- **Problem:** Casting `*const PCell<T>` to `*const T` does not semantically project the cell's `ucell` storage. It depends on an unstated, unguaranteed layout coincidence for a `repr(Rust)` wrapper; if the stored field is not at offset zero, dereferencing the advertised pointer accesses the wrong bytes. `#[verifier::external_body]` hides this executable premise from verification rather than establishing it.
- **Suggestion:** Obtain the raw pointer from the cell's actual storage using a supported `PCell` accessor. If vstd exposes no such accessor, add a narrowly reviewed accessor at the `PCell` abstraction boundary (with the required representation justification and contract) and call it here; do not cast the address of the wrapper. Preserve the original `UnsafeCell::get()` behavior shown by the commented source.

## Medium

### The new pointer API has no usable address/identity guarantee

- **Guidelines:** `api-postconditions`, `complete-external-contracts`
- **Location:** `ostd/src/sync/rwarc.rs:80-82`; trusted helper at `ostd/src/sync/rwlock.rs:633-636`
- **Evidence:** `RwArc::as_ptr` is documented only as “Returns a raw pointer to the contained value” but has no `ensures`/`returns` clause. Its `#[verifier::external_body]` helper likewise has no contract at all.
- **Problem:** The return value is the entire result of this getter, yet no specification connects it to the contained `T`, the `RwLock` cell identity, or stability across calls while the allocation remains alive. Verus may therefore treat the trusted helper's result as arbitrary, so a verified caller cannot establish the documented property or safely compose this pointer with another API that needs the contained object's address.
- **Suggestion:** Define an abstract address/identity model for the protected cell and give the trusted helper an exact result guarantee; propagate that guarantee through `RwArc::as_ptr` (prefer `returns` for an exact result). Keep aliasing and lock-state obligations at unsafe dereference sites rather than claiming that the raw pointer itself grants access.

## Low

No low-severity findings.

## Evidence check record

- Read all 154 lines of `diff.patch`; the only semantic additions are the public `RwArc::as_ptr` and its newly enabled/trusted `RwLock::as_ptr`. The remaining changes reorder fields/local bindings without changing expressions.
- Read the surrounding before/after definitions and call path in `ostd/src/sync/rwarc.rs` and `ostd/src/sync/rwlock.rs`. Confirmed that `RwLock::val` is `PCell<T>` and that existing dereference implementations obtain the stored value through `PCell::borrow`, whose implementation is described locally in terms of `self.ucell.get()`.
- Searched the scoped diff for `rlimit`: no added or changed `#[verifier::rlimit(...)]`, hence no `rlimit > 200` finding.
- The diff adds no external specification for a `std`, `core`, or `alloc` API, so the upstream-spec-reuse workflow check was not triggered.
- No duplicated existing spec/predicate suitable for reuse was found in the changed code; the required pointer identity model is absent rather than duplicated.
- **No-verification disclosure:** Per the requested fast-review constraints, no Verus build, proof experiment, isolated caller experiment, CI run, repository history inspection, or exhaustive guideline checklist was performed. Findings are based on static source evidence only.
