# Review: PR #439 snapshot

> Produced from the VOSTD coding guidelines and the skill's API-contract criteria.
> Scope: fast, non-exhaustive static review of the immutable `diff.patch`, with `before/` and `after/` used only for context.

**Bottom line:** The new `memcpy` path replaces a working runtime intrinsic with a recursive verified helper whose byte primitives execute `unimplemented!()`, so every non-empty VM copy now panics. The patch also introduces a second, axiom-only model of the `VmSpace` API and leaves the new volatile read/write boundary without the value-level contracts its callers need. These trust and contract gaps should be resolved before merge.

## High

### Non-empty VM copies now reach `unimplemented!()`

- **Guideline:** `preserve-exec-code`
- **Location:** `ostd/src/mm/io.rs:145` (with the failing primitive at `ostd/specs/mm/virt_mem_newer.rs:429`)
- **Evidence:** Before this change, `memcpy` executed `core::intrinsics::volatile_copy_memory(dst as *mut u8, src as *const u8, len)`. The new body is `VirtPtr::copy_nonoverlapping(&src, &dst, Tracked(mem_src), Tracked(mem_dst), len);`. For every `n > 0`, `copy_nonoverlapping` calls `copy_offset`, which calls `tmp.read(Tracked(mem))`; the newly added executable `VirtPtr::read` body is exactly `unimplemented!()` (`virt_mem_newer.rs:429-439`).
- **Problem:** This is not an executable-preserving packaging change: a non-empty `VmReader::read`/`VmWriter::write` copy follows this path and panics at the first byte instead of copying memory. `#[verifier::external_body]` trusts verification of the body; it does not provide a runtime implementation for `unimplemented!()`.
- **Suggestion:** Restore the original `volatile_copy_memory` executable body and specify that original operation at the trust boundary. If the recursive implementation is intentional, first replace `VirtPtr::read` and `VirtPtr::write` with real runtime byte loads/stores and retain the original implementation/provenance evidence required by `preserve-exec-code`.

## Medium

### The claimed `VmSpace` step theorem is proved from duplicate axioms rather than the verified API contracts

- **Guidelines:** `centralize-trusted-boundaries`, `reuse-existing-specifications`, `complete-external-contracts`
- **Location:** `ostd/specs/mm/vm_space_embedding.rs:179`
- **Evidence:** The new module states that each `_embedded` axiom merely “mirrors the `ensures` clause of one public exec function,” then introduces independent axioms such as `vm_space_new_embedded`, `vm_space_cursor_embedded`, `cursor_mut_map_embedded`, and `vm_space_writer_embedded` (`vm_space_embedding.rs:179-332`). `step` (`:339-365`) calls these axioms, not the actual API specifications. The comment explicitly requires future reviewers to manually update both copies when an exec `verus_spec` changes.
- **Problem:** This creates a second trusted source for facts already expressed by the real API contracts. The resulting `step` theorem establishes preservation for an axiom-defined transition system, not a mechanically connected abstraction of the executable API; contract drift can therefore leave the advertised “soundness theorem” verifying while the real API has different requirements or effects.
- **Suggestion:** Define the embedding transition relation from shared spec predicates used directly by the executable contracts, and prove `step` from verified lemmas over those predicates. Keep unavoidable external facts in the centralized external-spec layer rather than one axiom per local API method.

### Volatile reads and writes do not expose their value-level effects

- **Guideline:** `api-postconditions`
- **Location:** `ostd/specs/mm/virt_mem_newer.rs:476`
- **Evidence:** `read_volatile<T>` returns `T` but has only `requires` clauses and no `returns`/`ensures` tying the result to the initialized bytes (`virt_mem_newer.rs:476-490`). `write_volatile<T>` promises only that mappings are unchanged and the memory domain can grow (`:511-526`), not that the bytes encode `val`. Its natural caller `VmReader::read_once` returns `Ok(v)` from this value (`ostd/src/mm/io.rs:1298-1335`), yet that public contract likewise constrains only cursor movement, not `v`.
- **Problem:** Callers can prove that an access occurred and ownership advanced, but cannot prove what was read or written. This omits the principal functional promise of these APIs and makes the new memory model unusable for value correctness.
- **Suggestion:** Add a byte encoding/decoding abstraction for `PodOnce`; make `read_volatile` return the decoded bytes and make `write_volatile` update exactly the corresponding byte range while framing the remainder. Propagate the read result guarantee through `read_once`.

## Low

| Finding | Guideline | Detail |
|---|---|---|
| Centralize the new `core` pointer specification | `upstream-reusable-specs` | `ostd/src/mm/io.rs:87` adds a local `assume_specification` for `<*mut T>::is_aligned`. This models a reusable `core` API rather than an OSTD-specific operation; propose it for the shared/upstream Verus specification layer and consume that definition here. |

## Evidence check record

- Read `diff.patch` as the authoritative change and inspected the corresponding `before/` and `after/` source around every reported location.
- Traced the new non-empty copy path statically: `memcpy` → `VirtPtr::copy_nonoverlapping` → `copy_offset` → `VirtPtr::read` → `unimplemented!()`.
- Enumerated the added `_embedded` axioms and checked that `step` consumes those duplicate axioms rather than a shared predicate connected to the executable contracts.
- Checked the complete signatures and immediate natural callers of `read_volatile` and `write_volatile`; no other clause pins the read result or written byte values.
- No changed `#[verifier::rlimit(...)]` was present, so there is no `rlimit > 200` finding.
- **No-verification disclosure:** Per the requested fast-review scope, I did not run Verus, Rust builds, tests, history analysis, exhaustive rule coverage, or isolated caller experiments. Findings above are based solely on static source and before/after diff evidence.
