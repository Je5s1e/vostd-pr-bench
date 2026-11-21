# Review: PR #915 snapshot (`diff.patch`)

> Produced from the VOSTD maintainability, proof-engineering, workflow, and API-contract criteria.
> Scope: `pr-915-7a42b67bb385/diff.patch` is the authoritative change set; files under `before/` and `after/` were used only for surrounding context. Per the fast-review request, history, exhaustive rule enumeration, Verus/CI runs, caller experiments, and subagent passes were not performed.

**Bottom line:** The newly verified address conversions prove their bodies by assuming range predicates that are false for values admitted by their own public `From<usize>` implementations. Because these assumptions occur inside ordinary safe, generic `From` conversions, any verified caller can reach them with an unrestricted value and make the proof context inconsistent. This is a trust-boundary and API-contract blocker; the range must be established structurally or checked at the input boundary rather than assumed locally.

## High

### Unrestricted values reach unconditional trusted range assumptions

- **Guidelines:** `centralize-trusted-boundaries`, `api-preconditions`, `api-postconditions`
- **Location:** `ostd/libs/linux-bzimage/builder/src/mapping.rs:124` (especially lines 125–138), and `ostd/libs/linux-bzimage/builder/src/mapping.rs:143` (especially lines 144–155)
- **Evidence:** The module exposes unrestricted construction with `impl From<usize> for SetupVA` and `impl From<usize> for SetupFileOffset` (lines 48–53 and 86–91). Nevertheless, the first cross-type conversion executes `assume(SETUP32_LMA - LEGACY_SETUP_SEC_SIZE <= va.addr <= usize::MAX - LEGACY_SETUP_SEC_SIZE);` (line 134), and the reverse conversion executes `assume(offset.offset <= usize::MAX - SETUP32_LMA);` (line 152). The module documentation itself confirms that “unrestricted integer construction does not enforce” these ranges (lines 9–10). The formal postconditions are only implications (lines 125–129 and 144–148), while both `FromSpecImpl` instances declare `obeys_from_spec() -> bool { true }` (lines 162–179).
- **Problem:** These are not facts about every `SetupVA` or `SetupFileOffset`; for example, `SetupVA::from(0)` violates the first assumed lower bound, and `SetupFileOffset::from(usize::MAX)` violates the second assumed upper bound. Putting the assumptions inside safe `From` implementations allows an arbitrary verified caller to introduce a false proposition, after which unrelated obligations can be proved. The conditional result clauses do not contain the damage because the unconditional `assume` is available while verifying the function body, and the total-looking `From` API does not require callers to establish the antecedent.
- **Suggestion:** Remove both local assumptions. Encode valid mapped addresses/offsets in construction—e.g. checked `TryFrom<usize>`/validated constructors plus a representation invariant—and make the cross-type conversion available only for validated values; alternatively make the conversion itself checked and return `Option`/`Result`. If ELF provenance truly must remain trusted, centralize that fact at the ELF-validation boundary (or in the designated external-spec boundary) and return a validated mapping type from that boundary. Give the resulting API an unconditional exact postcondition for successful conversion; do not advertise an unrestricted, always-obeying `FromSpecImpl` unless the operation is total for every constructible source value.

## Medium

No medium-severity findings.

## Low

No low-severity findings.

## Evidence check record

- Read all 575 lines of the authoritative `diff.patch` and the complete before/after `mapping.rs` files.
- Checked direct callers in `builder/src/lib.rs:91–93` and `builder/src/pe_header.rs:368–375`; both obtain values from ELF data, but neither changes the fact that the public constructors admit arbitrary `usize` values and the conversion implementations assume the ranges unconditionally.
- Searched the scoped patch and after-tree for `assume`, `admit`, `external_body`, and `rlimit`. The only scoped trust operations are the two assumptions reported above; no changed `#[verifier::rlimit(...)]` exists, so the `rlimit > 200` workflow check did not trigger.
- The patch adds no external specification for a `std`, `core`, or `alloc` API, so the upstreamable-spec workflow check did not trigger. The added `FromSpecImpl`, `AddSpecImpl`, and `SubSpecImpl` implementations reuse vstd interfaces rather than introducing a parallel interface.
- No Verus verification, compilation, CI run, runtime test, or isolated caller experiment was performed, as required by the fast-review override. Findings are based solely on static source and contract evidence.
