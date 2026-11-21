# Review: PR 809 fast isolated diff

> Scope: `diff.patch` is authoritative, with `before/` and `after/` used only for surrounding context. The patch changes `ostd/src/util/range_alloc.rs`, `verified_libs/vstd_extra/src/resource/mod.rs`, and `verified_libs/vstd_extra/src/resource/range.rs`.

**Bottom line:** The patch breaks the existing static `RangeAllocator` initialization by changing its constructor from `const fn` to `fn` without changing the static caller. This is a merge-blocking executable regression, independently of the proof changes. The new `alloc_specific` contract also does not expose the availability/success equivalence that its rustdoc calls a verified property.

## High

### Preserve the constructor's const-callable API, or migrate its static caller

- **Guideline:** `preserve-exec-code`
- **Location:** `ostd/src/util/range_alloc.rs:175-179`
- **Quoted evidence:** The patch says, “this constructor cannot remain const” and changes `pub const fn new(...)` to `pub fn new(...)`. However, the unchanged caller at `ostd/src/mm/kspace/kvirt_area.rs:143` remains `exec static KVIRT_AREA_ALLOCATOR: RangeAllocator = RangeAllocator::new(VMALLOC_VADDR_RANGE);`.
- **Problem:** A Rust static initializer cannot call a non-const function. The proof-driven constructor rewrite therefore leaves an existing executable caller ill-formed and prevents the affected target from compiling.
- **Suggestion:** Keep a const-callable construction path, or migrate `KVIRT_AREA_ALLOCATOR` to a supported lazy-initialization mechanism and update all uses accordingly. Do not land the non-const API change while the static initializer remains.

## Medium

### Specify the documented success/failure condition of `alloc_specific`

- **Guideline:** `api-postconditions`
- **Location:** `ostd/src/util/range_alloc.rs:224-247`
- **Quoted evidence:** The rustdoc claims, “Returns `Ok` if and only if the shared state's free list covers `allocate_range`.” The contract only ensures `res is Ok <==> allocated@ is Some` and constrains the token when it is present; it contains no pre-state availability predicate or free-set snapshot.
- **Problem:** The caller-visible contract allows an implementation to return `Err` despite a covering free block, provided it also emits no token. Thus the stated functional-correctness property is not available to verified callers, even though the implementation contains an internal completeness proof.
- **Suggestion:** Introduce a caller-usable abstract pre-state availability predicate or snapshot and ensure `res is Ok` exactly when that pre-state covers `allocate_range`; retain the token identity/range guarantees as the ownership result.

## Low

No findings.

## Evidence check record

- Read all 1,215 lines of `diff.patch` and inspected the corresponding before/after context for every changed path.
- Confirmed from the before/after snapshots that `RangeAllocator::new` changed from `const fn` to `fn`, while the static call at `ostd/src/mm/kspace/kvirt_area.rs:143` is unchanged.
- Checked the new `alloc_specific` rustdoc, its complete `#[verus_spec]` contract, its internal free-list search, and its internal completeness argument. The availability equivalence is proved only inside the implementation and is absent from the public postcondition.
- No `#[verifier::rlimit(...)]` change appears in the authoritative diff, and no new or materially changed external specification for a `std`, `core`, or `alloc` API appears.
- The repository snapshot does not contain the live `docs/coding-guidelines` pages; the review therefore used the skill's named `preserve-exec-code` rule and its explicit `api-postconditions` criterion.
- Per the fast-review instruction, no Verus run, build, history inspection, exhaustive rule enumeration, caller experiment, or other dynamic verification was performed. Findings are based on static source evidence only.
