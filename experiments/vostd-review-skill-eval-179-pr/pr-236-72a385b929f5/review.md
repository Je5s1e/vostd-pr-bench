# Review: PR 236 snapshot `0e826a358beea7bf892e63b9a50290300aa0437c..72a385b929f527e0014e13b3e93950d5ec4fde20`

> Fast, non-exhaustive VOSTD review of `diff.patch`, with the exported before/after trees used only as source context. The reviewed patch changes `Cargo.toml`, four member manifests, and `vstd_extra/src/ptr_extra.rs`.

**Bottom line:** The patch leaves the Cargo workspace invalid. It removes `verus_builtin` and `verus_builtin_macros` from `[workspace.dependencies]` but does not remove the unchanged inherited references from the `demo` workspace member, so Cargo cannot load the workspace. This should block merging until the `demo` manifest is updated consistently.

## High

### The workspace dependency cleanup omits the `demo` member

- **Area:** Maintainability / workspace dependency contract
- **Location:** `Cargo.toml:31`; supporting context at `Cargo.toml:5` and `demo/Cargo.toml:25-26`
- **Evidence:** The patch changes the root table from

  ```toml
  [workspace.dependencies]
  # Verus
  vstd = { path = "tools/verus/source/vstd" }
  verus_builtin = { package = "verus_builtin", path = "tools/verus/source/builtin" }
  verus_builtin_macros = { package = "verus_builtin_macros", path = "tools/verus/source/builtin_macros" }
  ```

  to

  ```toml
  [workspace.dependencies]
  # Verus
  vstd = { path = "tools/verus/source/vstd" }
  ```

  However, the after tree still lists `demo` as a workspace member and its unchanged manifest still contains:

  ```toml
  verus_builtin = { workspace = true }
  verus_builtin_macros = { workspace = true }
  ```

  A static search of all after-tree `Cargo.toml` files finds these as the only remaining inherited references.
- **Problem:** A member dependency with `workspace = true` requires a matching entry in the root `[workspace.dependencies]` table. Because both definitions were removed at the root while `demo` still inherits them, Cargo manifest loading fails before build or Verus verification can start.
- **Suggestion:** Remove the two stale dependency entries from `demo/Cargo.toml` as part of this patch (they have no matching Rust references in the exported after tree), and update the lockfile if the repository tracks the resulting dependency graph. Alternatively, retain the two root workspace dependency definitions until every member has migrated away from them.

## Medium

No evidence-backed medium-severity findings.

## Low

No useful low-severity findings.

## Evidence check record

- Read all 70 lines of `diff.patch` and inspected the corresponding before/after manifests and `vstd_extra/src/ptr_extra.rs`.
- Confirmed statically that `demo` remains in the root workspace (`Cargo.toml:5`).
- Confirmed by byte comparison that `demo/Cargo.toml` is unchanged between the before and after snapshots.
- Searched all after-tree Cargo manifests: only `demo/Cargo.toml:25-26` still inherits `verus_builtin` or `verus_builtin_macros` after their root definitions are deleted.
- Searched the after-tree Rust and manifest context and found no Rust references to either removed crate; this supports removing the two stale `demo` manifest entries rather than restoring the root definitions.
- No changed `#[verifier::rlimit(...)]` attribute was present, so there is no `rlimit > 200` finding.
- No external specification for a `std`, `core`, or `alloc` API was added or materially changed, so the upstream spec-reuse check was not triggered.
- The patch changes no executable/proof API contract, invariants, assumptions, admits, or trust-boundary annotations; no separate proof/trust or API-contract finding was supported.
- **No-verification disclosure:** Per the fast-review scope, no Cargo command, Verus verification, proof experiment, history inspection, or isolated caller experiment was run. The merge-blocking conclusion follows from Cargo's manifest inheritance contract and the quoted before/after source evidence; CI status was not independently verified.
