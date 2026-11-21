# Review: PR 501 snapshot `5646c42516b4`

> Produced from the VOSTD coding-guideline criteria and the skill's API-contract criteria.
> Scope: fast, non-exhaustive static review of authoritative `diff.patch`, with the supplied `before/` and `after/` trees used only for context.

**Bottom line:** The newly added `VmSpace::activate` is not a usable activation API. Existing clients cannot call it with the method syntax and `Arc<VmSpace>` representation already used by this module, while an associated call that supplies the declared `RoArc` argument unconditionally panics. This is a merge-blocking incomplete scaffold, and the trusted `external_body` also exposes no formal activation guarantee to verified callers.

## High

### `VmSpace::activate` is neither callable by its intended clients nor implemented

**Guidelines:** `api-preconditions`, `api-postconditions`  
**Location:** `ostd/src/mm/vm_space.rs:316`

**Evidence:**

```rust
/// Activates the page table on the current CPU.
#[verifier::external_body]
pub fn activate(this: &RoArc<Self>) {
    // ...
    // self.pt.activate();
    unimplemented!()
}
```

The parameter is named `this`, not `self`, so this is an associated function rather than a method. The supplied after-tree nevertheless contains natural clients such as `ostd/src/mm/test.rs:662`:

```rust
let vmspace = Arc::new(VmSpace::new());
vmspace.activate();
assert_eq!(get_activated_vm_space(), Arc::as_ptr(&vmspace));
```

The commented intended implementation also still uses `Arc::as_ptr(self)` and `Arc::clone(self)`, which do not match the new `&RoArc<Self>` parameter. Even an explicit `VmSpace::activate(&ro_arc)` call reaches `unimplemented!()` and cannot establish the documented effect. Because there is no `#[verus_spec]`, `ensures`, or other callable contract, verified clients likewise receive no fact that the page table or CPU activation state changed.

**Suggestion:** Complete the executable activation path before exposing this function. Preserve the existing client-facing ownership model (the surrounding code and tests use `Arc<VmSpace>`) and make it an actual receiver, or migrate all clients and the implementation coherently if `RoArc` is an intentional API change. Then give the trusted boundary an explicit contract that models the documented activation effect and any required CPU/preemption conditions; do not retain `unimplemented!()` behind `external_body`.

## Medium

No evidence-backed medium-severity findings.

## Low

No useful low-severity findings.

## Evidence check record

- Read all 55 lines of `diff.patch`; it changes only `ostd/src/mm/vm_space.rs` and adds no `#[verifier::rlimit(...)]` or external specification for a `std`, `core`, or `alloc` API.
- Compared the changed hunk with `before/ostd/src/mm/vm_space.rs` and inspected the corresponding after-tree context at lines 280–370.
- Searched the supplied after-tree for activation clients and related implementations. The concrete clients at `ostd/src/mm/test.rs:662`, `:667`, and `:753` call `.activate()` on values created with `Arc::new(VmSpace::new())`; no `RoArc<VmSpace>` client was found. The lower-level `PageTable<UserPtConfig>::activate` implementation is itself commented out at `ostd/src/mm/page_table/mod.rs:1104-1113`.
- The finding was checked against Rust receiver syntax and the exact supplied source. The recommendation preserves the intended activation semantics expressed by the rustdoc, tests, and commented implementation rather than guessing a new model.
- Per the requested fast-review override, no Verus run, Rust build, CI run, caller experiment, repository history inspection, or exhaustive guideline checklist was performed. Conclusions are static and limited to the supplied snapshot.
