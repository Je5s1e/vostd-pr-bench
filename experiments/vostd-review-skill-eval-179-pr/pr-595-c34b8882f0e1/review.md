# Review: `diff.patch` (`dv` 5de8011be6322698f986be02de2858af8756fc59..4f29d1d95a3af37d93867e87f0360dfb3ec2276)

> Produced by a fast, non-exhaustive VOSTD review of the supplied patch and its supplied before/after context.
> Scope: `Makefile`, `README.md`, and the updated `dv` gitlink, with `before/dv` and `after/dv` used to inspect the gitlink change.

**Bottom line:** The `dv` rewrite keeps accepting and documenting CLI options that its new `cargo-verus` delegation silently ignores. That is a user-visible command contract regression and should be fixed before merge. No changed Verus code, proof/trust boundary, assumptions, invariants, external specifications, or `rlimit` attributes were present in the reviewed patch.

## High

None.

## Medium

### `cargo dv verify/compile` silently ignore accepted options

- **Guideline:** `api-postconditions`
- **Location:** `dv/src/main.rs:450` and `dv/src/main.rs:492`
- **Evidence:** `VerifyArgs` still declares `--import` with the help text `"Import verified local crates (they need to be compiled first)"` (`dv/src/main.rs:148-155`), and `CompileArgs` declares the same option (`dv/src/main.rs:253-260`) plus `--disasm` (`dv/src/main.rs:295-301`). Before the gitlink update, `verify` and `compile` cloned `args.imports` and passed it to `exec_verify`/`exec_compile`; after the update, both handoffs omit `args.imports`. The new `exec_compile` builds a `cargo-verus build` command from release/log/trace/max-errors/pass-through fields but never reads `options.disasm` (`dv/src/verus.rs:955-1005`).
- **Problem:** The CLI successfully parses these flags and promises effects in `--help`, but the command now behaves exactly as if they were absent. Callers can therefore receive a successful command with requested imports or disassembly silently omitted.
- **Suggestion:** Either translate each retained option into the corresponding `cargo-verus` invocation/output step and add delegation tests, or remove/reject unsupported options explicitly so their requested effect cannot be mistaken for a successful one. In particular, do not leave `--import` and `--disasm` as accepted no-ops.

## Low

None.

## Evidence check record

- Read `diff.patch` in full and compared the supplied `before`/`after` versions of `Makefile`, `README.md`, `dv/src/main.rs`, `dv/src/verus.rs`, and `dv/src/console.rs`.
- Confirmed statically that `--import` remains part of both argument structs but neither `verify` nor `compile` reads `args.imports` after the update.
- Confirmed statically that `--disasm` still populates `ExtraOptions::disasm`, while the replacement `exec_compile` never reads that field.
- Confirmed that command failures are not silently swallowed: the local `error!` macro exits the process. This does not refute the accepted-no-op option issue.
- The patch contains no changed Verus source, contracts, proofs, assumptions, invariants, external `std`/`core`/`alloc` specifications, or `#[verifier::rlimit(...)]`; proof-engineering, trust-boundary, invariant, spec-reuse, and `rlimit > 200` checks therefore produced no findings.
- Per the requested fast-review constraints, no build, Verus run, caller experiment, history inspection, or exhaustive guideline pass was performed. Findings are based on static evidence only and have not been execution-verified.
