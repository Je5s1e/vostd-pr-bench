# Review: `diff.patch` (`before` → `after` snapshots)

> Produced from the supplied VOSTD review skill, `diff.patch`, and the matching before/after source snapshots.
> Scope: authoritative patch SHA-256 `d6129143d3f8201bfea95035780acdd9f1b32edc639de19a5935be01ddd03d5d`; changed files `ostd/src/arch/x86/ex_table.rs` and `ostd/src/arch/x86/mod.rs`.

**Bottom line:** The lookup contract is caller-usable and describes the first matching exception-table entry without an apparent precondition or postcondition gap. The main issue is architectural: the patch introduces an uninterpreted model and an `external_body` axiom in the executable module next to the verified caller, expanding a locally owned trust boundary instead of centralizing it. No high-severity issue was found in the supplied patch.

## High

None.

## Medium

### Centralize the exception-table trust boundary

- **Guideline:** `centralize-trusted-boundaries`
- **Location:** `ostd/src/arch/x86/ex_table.rs:23`, `ostd/src/arch/x86/ex_table.rs:125`
- **Quoted evidence:** `pub uninterp spec fn table_model() -> Seq<(Vaddr, Vaddr)>;` and `#[verifier::external_body] ... fn read_table() -> &'static [ExTableItem]`
- **Problem:** The sole axiom connecting linker memory to the logical table is declared in the same executable module as `find_recovery_inst_addr`. This makes a caller-owned module the authority for both the trusted fact and the proof that consumes it, contrary to the guideline's requirement to isolate trusted facts in a dedicated boundary layer.
- **Suggestion:** Move the linker-section model and its trusted contract into a dedicated x86 specification/boundary module (for example under `ostd/specs/arch/x86/`), expose only the narrow modeled read operation, and have `ex_table.rs` consume that operation. Keep the unsafe linker-symbol implementation thin and retain the documented alignment, initialization, immutability, ordering, divisibility, and `isize::MAX` assumptions at the owning boundary.

## Low

| Finding | Guideline | Detail |
|---|---|---|
| Preserve the original import | `preserve-exec-code` | At `ostd/src/arch/x86/ex_table.rs:4`, the new comment says `` `crate::prelude` is disabled ``, but `after/ostd/src/lib.rs:52` still contains `pub mod prelude;`. The patch replaces `use crate::prelude::Vaddr;` with `use crate::mm::Vaddr;` solely for the proof conversion. Restore the original `Vaddr` import and keep the added `vstd` import separate; if the original import genuinely fails in the intended build, state and demonstrate that concrete obstacle instead of recording an inaccurate reason. |

## Evidence check record

- Read all 128 lines of authoritative `diff.patch` and compared both changed files against their supplied before/after snapshots.
- Confirmed that `ostd/src/arch/x86/mod.rs:5-8` only enables `ex_table` while leaving the surrounding previously commented modules commented; this is not a runtime module-removal finding.
- Checked the `find_recovery_inst_addr` contract statically. A `Some(recovery)` result is tied to an in-range matching entry with all earlier entries non-matching, while `None` is equivalent to absence of any match; no natural-client precondition or postcondition gap was identified.
- Searched the supplied `after` tree for `table_model`, `find_recovery_inst_addr`, and `ExTableItem`. No existing reusable exception-table model was found; the only runtime caller found is `ostd/src/arch/x86/trap/mod.rs:231`.
- Searched the authoritative patch for `#[verifier::rlimit(...)]`; none was added or changed, so the numeric `rlimit > 200` workflow check was not triggered. No new or materially changed external specification for a `std`, `core`, or `alloc` API was present.
- The snapshots contain no `AGENTS.md`, so this review cannot establish whether the newly introduced `external_body` received the separate authorization referenced by the maintainability guidance. That unknown is recorded here rather than promoted to a finding.
- **No-verification disclosure:** Per the fast-review override, no Verus run, Cargo build, test, history inspection, exhaustive rule enumeration, or isolated caller experiment was performed. Findings are based only on static evidence in `diff.patch`, the before/after context, and the supplied review-skill guidance.
