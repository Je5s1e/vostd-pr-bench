# Review: PR #226 `diff.patch` scope (snapshot)

> Produced from the VOSTD review skill's proof-engineering and API-contract criteria.
> Scope: `diff 24bb2dfe8076ab5a4b37f0c3324fe566a24dfe17..84f7a7f07d36f015a588bb8a5d1910e06384b11c`; only the two files and hunks captured in `diff.patch`, with `before/` and `after/` used for context.

**Bottom line:** The patch introduces three new trusted proof boundaries in code that is otherwise small enough to verify directly. Most importantly, `push` is both trusted and specified too narrowly: its contract rules out the documented full-array/`Err` behavior and does not expose the successful abstract state update. These issues should be resolved before merge so later proofs do not build on admitted or incomplete behavior.

## High

### The view invariant is admitted

- **Guideline:** `centralize-trusted-boundaries`
- **Location:** `ostd/src/boot/memory_region.rs:81`
- **Evidence:** The patch changes an empty proof body to `proof fn view_preserves_inv(self) { admit(); }`. The concrete invariant is `self.base + self.len <= CONST_MAX_PADDR`, while the view is `MemRegionModel { base: self.base as int, end: self.base + self.len, typ: self.typ.to_int() }`; the model invariant is stated at `specs/ostd/src/memory_region_specs.rs:13-16`.
- **Problem:** `admit()` makes every user of `InvView` trust that the executable region's view satisfies `MemRegionModel::inv()`. This is precisely the bridge that should establish the address and type bounds, so leaving it admitted defeats the purpose of adding the invariant.
- **Suggestion:** Prove the bounds from `self.inv()`, the `usize`/address facts, and the exhaustive `MemoryRegionType::to_int` mapping. If a reusable enum-range lemma is needed, add and prove that lemma rather than admitting this bridge.

### The empty constructor is replaced by a trusted body

- **Guideline:** `centralize-trusted-boundaries`
- **Location:** `ostd/src/boot/memory_region.rs:280`
- **Evidence:** The patch adds `#[verus_verify(external_body)]` to `MemoryRegionArray::new` while promising both `ret.inv()` and `ret@ == MemoryRegionArrayModel::<LEN>::new()`; it simultaneously removes the prior in-body proof assertion. The implementation is only an array of `MemoryRegion::bad()` with `count: 0` (`:286-293`).
- **Problem:** The exact empty-sequence model and representation invariant are now axioms at every call site even though this constructor has a direct, deterministic body. This unnecessarily enlarges the trusted computing base for the foundational constructor and for the newly verified `Default` implementation.
- **Suggestion:** Remove `external_body` and prove that `count == 0` makes the view `Seq::empty()` and satisfies `count <= LEN`; keep any small sequence equality as an ordinary proof assertion.

### `push` trusts an incomplete contract that excludes documented behavior

- **Guidelines:** `centralize-trusted-boundaries`, `api-preconditions`, `api-postconditions`
- **Location:** `ostd/src/boot/memory_region.rs:295`
- **Evidence:** The rustdoc says, “If the set is full, an error is returned,” and the body has an `Err("MemoryRegionArray is full")` branch. However, the new contract requires `!old(self)@.full()`, ensures `ret.is_ok()`, leaves `self@ == old(self)@.push(region@)` commented out, and the function is marked `#[verus_verify(external_body)]` (`:298-315`).
- **Problem:** A safe fallible call on a full array is part of the documented API, but the precondition makes that call illegal in verified code. On the accepted success path, callers learn neither that the region was appended nor that the prior elements were preserved; meanwhile the entire mutation is trusted rather than checked.
- **Suggestion:** Remove `external_body` and verify both branches. Require only the valid input state and `region.inv()`; ensure the invariant, return `Ok` with `self@ == old(self)@.push(region@)` exactly when the old array is not full, and return `Err` with `self@ == old(self)@` when it is full.

## Medium

None.

## Low

None.

## Evidence check record

- Read all 159 lines of `diff.patch` and compared the complete affected definitions in `before/` and `after/`.
- Checked the changed model, concrete invariants, view functions, constructor, `Default`, `push` documentation, contract, and both executable branches. The proposed `push` correction preserves the implementation's existing success/failure split and does not assume a representation beyond the public sequence model already introduced by the patch.
- Searched the scoped patch for `admit`, `external_body`, and `rlimit`: it adds one `admit`, two `external_body` attributes, and no `#[verifier::rlimit(...)]`; therefore there is no `rlimit > 200` finding. The patch adds no external specification for a `std`, `core`, or `alloc` API, so the upstream-spec-reuse workflow check is not triggered.
- No duplicate existing specification was identified from the scoped names; `MemoryRegionArrayModel::push` is the model operation intended by the commented postcondition rather than an additional trusted external spec.
- **No-verification disclosure:** This was the requested fast, non-exhaustive static review. No Verus run, isolated caller experiment, CI run, repository history analysis, or exhaustive guideline enumeration was performed; findings are based only on `diff.patch` plus the supplied before/after context.
