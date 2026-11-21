# Review: PR 782 snapshot `4f44ff343670`

> Scope: authoritative `diff.patch`, with `before/` and `after/` used only for surrounding context. The patch changes `ostd/src/boot/memory_region.rs`, replacing an explicit `Inv` contract with a type invariant and enabling a verified `Deref` implementation.

**Bottom line:** The new type invariant and `Deref` contract are internally consistent, but the edited `push` API still requires the array not to be full even though its documentation and executable implementation define a supported full-array outcome. This prevents verified callers from using the advertised fallible behavior and should be fixed before merge.

## High

No high-severity findings.

## Medium

### The `push` contract excludes its documented error case

- **Guideline:** `api-preconditions`
- **Location:** `ostd/src/boot/memory_region.rs:298`
- **Evidence:** The documentation says, `If the set is full, an error is returned.` The edited contract nevertheless requires `!old(self)@.full()` at line 301 and guarantees only `ret.is_ok()` at line 304. The implementation has an explicit full-array branch, `Err("MemoryRegionArray is full")`, at lines 319-320.
- **Problem:** A verified caller cannot call `push` when the array is full, so the formal API rejects exactly the input for which the documented fallible behavior exists. This is not needed for memory safety: the implementation checks `self.count < self.regions.len()` before indexing, and the newly introduced type invariant establishes `self.count <= LEN`.
- **Suggestion:** Remove `!old(self)@.full()` and specify both outcomes. When `old(self)@.full()`, require `final(self)@ == old(self)@` and `ret.is_err()`; otherwise require `final(self)@ == old(self)@.push(region@)` and `ret.is_ok()`. Preserve `region.inv()` unless a separate soundness review establishes that it is unnecessary.

## Low

No low-severity findings.

## Evidence check record

- Read all 83 lines of `diff.patch`; it is the authoritative change set.
- Compared the changed region against `before/ostd/src/boot/memory_region.rs` and `after/ostd/src/boot/memory_region.rs`, including the full `MemoryRegionArray` implementation and its model in `ostd/specs/mm/frame/memory_region_specs.rs`.
- Confirmed statically that the new type invariant is `self.count <= LEN`, the backing array length is `LEN`, and `push` checks the bound before indexing.
- Confirmed that the new `Deref` postcondition pins both slice length and every element's view to `self@.regions`; no unsupported contract gap was identified there.
- No `#[verifier::rlimit(...)]` change is present, and the patch does not add or materially change an external specification for a `std`, `core`, or `alloc` API.
- Per the requested fast-review constraints, no Verus run, caller experiment, history inspection, exhaustive guideline pass, or subagent/persona pass was performed. Findings are based on static source and contract evidence only.
