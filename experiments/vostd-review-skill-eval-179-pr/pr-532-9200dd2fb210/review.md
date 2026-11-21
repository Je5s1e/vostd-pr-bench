# Review: PR 532 snapshot (`diff.patch`)

> Produced by a fast, non-exhaustive static VOSTD review of the supplied patch and its `before/` / `after/` context.
> Scope: `/Users/chao/workspace/REvolve/vostd-pr-test/pr-532-9200dd2fb210/diff.patch`; no repository history, Verus run, CI run, or isolated caller experiment was performed.

**Bottom line:** The patch is not ready to merge because it expands the trusted proof surface in core page-table cursor code: it adds a new `external_body` to a previously checked helper and introduces numerous `assume(...)` statements to discharge cursor invariants and API proof obligations. It also raises two already excessive solver limits and globally suppresses warnings for the verification target. The strongest issue is the trust regression, because the affected assumptions directly support the contracts of unsafe mapping and unmapping operations.

## High

### Newly admitted page-table cursor correctness

- **Guideline:** `centralize-trusted-boundaries`
- **Location:** `ostd/src/mm/page_table/cursor/mod.rs:2418` (with further examples at `ostd/src/mm/page_table/cursor/locking.rs:165,192-211` and `ostd/src/mm/page_table/cursor/mod.rs:3464`)
- **Evidence:** The patch adds `#[verifier::external_body]` to `map_branch_pt`, immediately before a contract that promises preservation of `invariants`, `in_locked_range`, cursor position, the complete owner view, and metadata regions. It also adds proof admissions such as `assume(res.0.invariants(*res.1, *regions, *guards) ...);`, `assume(res.0.guard_level == C::NR_LEVELS());`, and `assume(absent_entry_owner.inv());`. The patch contains 22 added `assume(...)` occurrences and one added `external_body`; comments explicitly label several premises as `UNPROVABLE` or say that locking details are “being admitted here.”
- **Problem:** These admissions make the new caller-visible contracts true by trust rather than proof. In particular, downstream unsafe `map` / `take_next` reasoning can consume cursor, ownership, mapping, and lock invariants that the implementation has not established, so successful verification would not demonstrate the advertised safety properties.
- **Suggestion:** Do not merge these admissions. Strengthen the narrow external specifications that currently omit the physical-level/ghost-level relationships, add verified bridge and invariant-preservation lemmas for the tracked decomposition steps, and keep `map_branch_pt` verified. If a temporary trusted boundary is unavoidable, move the smallest auditable fact into the designated external-spec boundary with a documented soundness argument instead of admitting whole cursor postconditions or an entire executable helper.

## Medium

### Raised solver limits remain far above the project cap

- **Guideline:** `decompose-before-raising-rlimit`
- **Locations:** `ostd/specs/mm/page_table/mod.rs:1423`; `ostd/src/mm/page_table/cursor/mod.rs:3431`
- **Evidence:** `to_path_vaddr` changes from `#[verifier::rlimit(400)]` to `#[verifier::rlimit(1200)]`, and `take_next` changes from `#[verifier::rlimit(1000)]` to `#[verifier::rlimit(1500)]`. Both new values exceed the guideline cap of 200.
- **Problem:** The changed limits violate the workflow cap and make these proofs substantially more expensive and brittle.
- **Suggestion:** Refactor the proof obligations so each item stays at or below `rlimit(200)`, extracting focused lemmas or proof steps as needed, before retaining either increase.

### Verification globally hides compiler warnings

- **Guideline:** `narrow-lint-suppressions`
- **Location:** `Makefile:14`
- **Evidence:** The verification recipe changes from `cargo dv verify --targets $(VERIFICATION_TARGETS)` to `cargo dv verify --targets $(VERIFICATION_TARGETS) -- -Awarnings`.
- **Problem:** `-Awarnings` suppresses every warning across every verification target, including unrelated and future diagnostics, rather than documenting and scoping a known warning at the responsible item.
- **Suggestion:** Remove the global flag. Fix the warnings introduced by this patch, or apply a narrow item-level `#[expect(...)]` / targeted allowance for each deliberately retained diagnostic.

## Low

No evidence-backed low-severity findings.

## Evidence check record

- Read the complete supplied `diff.patch` scope structurally and inspected all changed paths, addition/deletion counts, added trust constructs, changed rlimits, and relevant `before/` / `after/` source context.
- Confirmed from the before/after diff that `map_branch_pt` newly gains `#[verifier::external_body]`; this is not an inherited annotation.
- Confirmed 22 added textual `assume(...)` occurrences and inspected representative uses that establish cursor invariants, ownership relations, bounds, and mapping facts.
- Confirmed the two changed rlimits and their old/new values directly from before/after source.
- Confirmed that the patch does not add or materially change a project-local external specification for a `std`, `core`, or `alloc` API, so no `upstream-reusable-specs` finding is reported.
- No additional strong API-precondition, API-postcondition, invariant-modeling, or specification-reuse finding was established from static evidence in this fast pass.
- **Verification disclosure:** Per the requested fast mode, this review did not inspect Git history, exhaustively enumerate every guideline rule, run Verus or CI, or perform isolated caller/contract experiments. Findings are based only on static patch and before/after evidence.
