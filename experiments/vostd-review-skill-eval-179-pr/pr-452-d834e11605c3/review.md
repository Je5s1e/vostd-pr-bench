# Review: PR #452 snapshot `d834e11605c3`

> Produced from the VOSTD coding-guideline rules and API-contract criteria applicable to this fast review.
> Scope: `diff.patch` was treated as the authoritative change set, with `before/` and `after/` used only for surrounding context. This is a fast, non-exhaustive static review; repository history, Verus runs, caller experiments, and CI verification were intentionally not performed.

**Bottom line:** The new typed-memory model places trusted volatile reads and writes behind public, unrestricted `Pod`/`PodOnce` bounds even though those traits do not establish the representation properties the trusted bodies require; this should block merging until the trusted generic boundary is restricted. The new kernel-memory axiom also mints a fully initialized `MemView` for an arbitrary range without requiring the range properties claimed by its documentation. In addition, three functions raise `rlimit` to 8000, and the newly added generally reusable `core` specifications have no recorded upstreaming plan.

## High

### The trusted typed-memory model accepts types that do not satisfy its representation assumptions

- **Guideline:** `restrict-generic-trusted-models`
- **Location:** `ostd/specs/mm/virt_mem.rs:553` (supporting declarations at `ostd/specs/mm/pod.rs:9`, `ostd/specs/mm/pod.rs:77`, and `ostd/specs/mm/pod.rs:86`)
- **Evidence:** `Pod` is declared only as `pub trait Pod: Copy + Sized`, and `PodOnce` only as `pub trait PodOnce: Pod`. Nevertheless, the changed code introduces `pub uninterp spec fn pod_bytes<T: Pod>(val: T)`, a generic injectivity axiom, and a trusted body `#[verifier::external_body] pub fn read_volatile<T: PodOnce>(...) -> (val: T)` whose result is related to arbitrary initialized bytes by `pod_bytes(val) == mem.read_bytes(...)`.
- **Problem:** Neither public safe trait states or enforces that every bit pattern is a valid `T`, that the type has the promised byte model, or that a volatile access is a valid single-instruction operation. A downstream crate can implement these public traits for a local `Copy` type containing restricted-validity fields, so the trusted generic body can perform a typed volatile read from bytes that are initialized but not a valid instance of that type. The new generic model therefore trusts semantic laws that the bound does not establish.
- **Suggestion:** Restrict the trusted surface to audited representations. Seal the traits or make the representation contract an explicit unsafe boundary, add a model-validity predicate admitted only for reviewed type/architecture combinations, and require that predicate on `pod_bytes`, `read_volatile`, and `write_volatile`. Do not expose the generic trusted contract on the strength of `Copy + Sized` alone.

## Medium

### `axiom_kernel_mem_view` grants an initialized mapping for any range

- **Guideline:** `complete-external-contracts`
- **Location:** `ostd/specs/mm/io.rs:49`
- **Evidence:** The documentation says the axiom covers “a kernel-VA range” and appeals to `[KERNEL_BASE_VADDR, KERNEL_END_VADDR)`, but its signature is `pub axiom fn axiom_kernel_mem_view(range: Range<usize>) -> (tracked mv: MemView)` with no `requires`. Its postcondition guarantees a translation, a memory entry, and `Init` for every `va` in the supplied range.
- **Problem:** Any proof caller can pass an arbitrary range and mint a tracked view asserting that every address in it is mapped and initialized. The contract omits the very kernel-range and validity premises used to justify this trust boundary, making the axiom substantially stronger than its rationale and its intended callers require.
- **Suggestion:** Add explicit requirements that the range is well formed, non-overflowing, within the kernel virtual-address interval, and backed by the relevant valid-borrow/mapping premise. Prefer consuming or borrowing an existing permission that establishes initialization instead of creating an unrelated fresh `MemView`; keep this trusted constructor in the centralized external boundary.

### Three changed functions exceed the permitted `rlimit` cap

- **Guideline:** `decompose-before-raising-rlimit`
- **Locations:** `ostd/src/mm/frame/segment.rs:568`, `ostd/src/mm/page_table/cursor/mod.rs:448`, `ostd/src/mm/page_table/cursor/mod.rs:1495`
- **Evidence:** Each scoped function has `#[verifier::rlimit(8000)]`; `query` previously used `#[verifier::rlimit(200)]`.
- **Problem:** The VOSTD workflow rule caps scoped `rlimit` values at 200. Each new value is 40 times that cap.
- **Suggestion:** Reduce each value to at most 200 before merge, restructuring the affected proofs as needed.

### The new standard-library specifications should be proposed upstream

- **Guideline:** `upstream-reusable-specs`
- **Locations:** `vstd_extra/src/external/int_specs.rs:9`, `vstd_extra/src/external/slice.rs:36`
- **Evidence:** The patch adds project-local specifications for the generic `core` APIs `u8/u16/u32/u64/usize::is_power_of_two`, `core::slice::from_raw_parts`, and `core::slice::from_raw_parts_mut`. No upstream proposal or upstreaming plan is recorded in the authoritative patch.
- **Problem:** These contracts are not OSTD-specific and are broadly reusable by Verus clients. Keeping them only in `vstd_extra` creates a second standard-library model that can drift from upstream Verus.
- **Suggestion:** Propose the integer and slice specifications upstream to Verus and record the upstream issue/PR in this change; keep any local copy explicitly temporary until the upstream model is available.

## Low

No strong low-severity findings.

## Evidence check record

- Read the complete authoritative `diff.patch` inventory and inspected before/after context for every reported location.
- Confirmed the three added/changed `rlimit` values statically and checked the prior `query` value shown by the patch.
- Traced the new `Pod` byte model into the trusted `VirtPtr::read_volatile`/`write_volatile` contracts and checked the actual public trait bounds.
- Checked the complete signature and postcondition of `axiom_kernel_mem_view` and its call sites in `ostd/src/mm/io.rs`.
- Inventoried the changed project-local external specifications for `core` APIs.
- Per the assigned fast-review scope, no repository history, exhaustive guideline pass, Verus execution, targeted caller experiment, or CI verification was performed. Findings are based on static source evidence only.
