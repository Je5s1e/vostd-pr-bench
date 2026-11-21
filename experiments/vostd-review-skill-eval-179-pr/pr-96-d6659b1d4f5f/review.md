# Review: PR 96 patch snapshot (`diff.patch`)

> Scope: `diff.patch` is the authoritative change set; `before/xtask/src/main.rs` and `after/xtask/src/main.rs` were used only for surrounding context.
>
> No verification was run: fast review mode explicitly excluded Verus, experiments, repository history, and exhaustive guideline checks.

**Bottom line:** The new Verus-root discovery does not establish the directory-layout invariant on which its callers rely. A valid `VERUS_PATH` or `PATH` entry that is a symlink, wrapper, or normally installed binary can therefore be accepted while producing an unrelated directory as the “source root,” breaking documentation and line-count commands. This should be fixed before merge.

## High

None.

## Medium

### The inferred source root is accepted without validating the Verus layout

- **Category:** API contract / path invariant (`api-postconditions`)
- **Location:** `xtask/src/main.rs:682`
- **Evidence:** `get_verus()` explicitly accepts a binary from `VERUS_PATH` or `PATH` (`locate(..., Some("VERUS_PATH"), ...)` at lines 109–116), but `get_verus_root()` merely walks up three parents and accepts the result when `root.is_dir()` (lines 683–690). Callers then assume source-tree-specific children exist, including `root/tools/line_count` (lines 546–550), `root/target/release/verusdoc` (lines 657–674), and `root/target-verus/debug/...` in `exec_doc`.
- **Problem:** Being an existing directory does not prove that the result is the Verus source root. For example, a `verus` symlink in a bin directory is not canonicalized, and an installed `/usr/local/bin/verus` produces `/usr` after three parent traversals; both satisfy `is_dir()` while pointing the subsequent commands at unrelated paths. This contradicts the existing lookup contract that advertises `VERUS_PATH` and `PATH` as supported ways to select the binary.
- **Suggestion:** Resolve symlinks before inference and validate source-root markers/required children rather than only `is_dir()`. If arbitrary installed or wrapped binaries cannot identify their source checkout reliably, add an explicit Verus-source-root override (with a default of `tools/verus/source`) and use it for source-dependent operations; keep binary discovery independent.

## Low

None.

## Evidence check record

- Read all 115 lines of the authoritative `diff.patch`.
- Compared the complete before/after file and inspected every changed caller of `get_verus_root()`, plus the existing `get_verus()` lookup order.
- Static refutation check: the new guard proves only that the third ancestor exists; no suffix check, canonicalization, source marker, or required-child validation establishes the claimed root.
- No `#[verifier::rlimit(...)]` change or new/materially changed `std`, `core`, or `alloc` external specification appears in the patch.
- No proof or trust-boundary code is changed. No API precondition issue was found beyond the postcondition/path-invariant defect above.
- No compilation, Verus verification, repository-history inspection, or isolated caller experiment was performed, per the requested fast-review constraints.
