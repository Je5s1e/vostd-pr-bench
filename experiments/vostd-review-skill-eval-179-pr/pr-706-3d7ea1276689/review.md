# Review: PR 706 captured patch

> Produced from the VOSTD coding-guideline criteria available through the review skill.
> Scope: fast, non-exhaustive static review of `diff.patch`, with `before/` and `after/` used only for surrounding context.

**Bottom line:** The change removes `IoPort`'s Rust `Drop` implementation and replaces it with an ordinary inherent method, so normal scope-based destruction no longer returns dynamically acquired ports to the allocator. It also opts the new `IoMem` `VmIo` implementation out of every caller-visible read/write postcondition even though the trait documents no-short-read/no-short-write behavior. The first issue is a blocking runtime resource-lifecycle regression; the second should be repaired before merging so verified callers can rely on the trait's promised behavior.

## High

### Automatic destruction no longer recycles acquired I/O ports

- **Guideline:** `preserve-exec-code`
- **Location:** `ostd/src/io/io_port/mod.rs:243`
- **Quoted evidence:** The base has `impl<T, A> Drop for IoPort<T, A> { fn drop(&mut self) { ... recycle(...) } }` at `before/ostd/src/io/io_port/mod.rs:80-90`. The new code comments that implementation out and adds only `pub fn drop(self)` at `after/ostd/src/io/io_port/mod.rs:243-278`.
- **Problem:** An inherent method named `drop` is not Rust's `Drop` trait and is not invoked when an `IoPort` goes out of scope. Consequently, an `IoPort` returned by `acquire` retains its allocator claim indefinitely unless every caller explicitly calls `port.drop()`, causing later acquisitions of that range to fail and breaking the former RAII behavior solely to accommodate verification.
- **Suggestion:** Restore the real `Drop` implementation and keep its executable behavior unchanged. If Verus cannot verify the lock-taking destructor, isolate that existing implementation as a narrowly documented trusted boundary (or add verifier support around it) rather than changing runtime destruction semantics.

## Medium

### `IoMem`'s `VmIo` contract makes the documented I/O guarantees vacuous

- **Guidelines:** `api-postconditions`, `complete-external-contracts`
- **Location:** `ostd/src/io/io_mem/mod.rs:267`
- **Quoted evidence:** The implementation defines `obeys_vmio_read_spec()` and `obeys_vmio_write_spec()` as `false`, and both `read_spec(...)` and `write_spec(...)` also return `false` (`after/ostd/src/io/io_mem/mod.rs:267-300`). The trait exposes an implementation's postcondition only through `Self::obeys_vmio_read_spec() ==> Self::read_spec(...)` and the analogous write implication (`after/ostd/src/mm/io.rs:1244-1255,1280-1291`), while its rustdoc promises that successful reads and writes consume the complete requested buffer (`after/ostd/src/mm/io.rs:1222-1228,1258-1264`). Both bodies are additionally trusted with `#[verifier::external_body]`.
- **Problem:** Because each `obeys_*_spec` flag is false, the implications are true without constraining the result, the final reader/writer cursor, or either tracked owner. A verified caller therefore cannot derive the documented no-short-read/no-short-write property—or any frame/ownership fact—from an `IoMem` call, while the trusted implementation is accepted without proving those effects.
- **Suggestion:** Make the relevant `obeys_vmio_*_spec` flags true and define `read_spec`/`write_spec` to expose the documented success behavior, result/error behavior, final cursor state, and preservation or update of both tracked owners. If hardware contents are intentionally nondeterministic, leave only the bytes' values unconstrained; do not discard the range, cursor, result, and ownership guarantees.

## Low

| Finding | Guideline | Detail |
|---|---|---|
| Propose the new `u32::to_le` specification upstream | `upstream-reusable-specs` | `verified_libs/vstd_extra/src/external/int_specs.rs:30-37` adds a generally reusable little-endian specification for the core integer API `u32::to_le`, but the captured change records no upstreaming plan. Propose this model to upstream Verus (or cite an existing upstream issue/PR) to avoid a long-lived project-local trust source. |

## Evidence check record

- Read all 3,409 lines of `diff.patch` and compared cited locations against the captured `before/` and `after/` files.
- Confirmed from the source that the removed implementation is the Rust `Drop` trait and the replacement is only an inherent `pub fn drop(self)` method.
- Confirmed that the `VmIo` trait guards its postconditions with `obeys_vmio_read_spec()` / `obeys_vmio_write_spec()` and that the new `IoMem` implementation sets both guards to `false`.
- No changed `#[verifier::rlimit(...)]` was present, so the `rlimit > 200` check was not triggered.
- The `u32::to_le` addition is a new project-local external specification for a core API and therefore triggered the narrow upstream-reuse check.
- **No-verification disclosure:** Per the requested fast-review mode, this review did not inspect git history, run Verus or CI, execute caller experiments, perform an exhaustive guideline checklist, or delegate persona passes. Findings are based solely on static evidence in the captured patch and before/after context.
