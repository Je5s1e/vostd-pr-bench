# Review: PR 76 isolated patch (diff.patch)

> Produced from the VOSTD coding guidelines and the skill's API-contract criteria.
> Scope: the authoritative `diff.patch`, with static before/after context for its four changed files. The patch changes `lock-protocol/src/exec/rw/cursor.rs`, `lock-protocol/src/exec/rw/mem_content/meta_slot/mod.rs`, `lock-protocol/src/exec/rw/node/mod.rs`, and `lock-protocol/src/mm/page_table/cursor/mod.rs`.

**Bottom line:** The pointer and cursor conversions are internally coherent in the inspected context, but they rewrite public executable representations and widen an executable constant for an internal verification caller. Under `preserve-exec-code`, this should be corrected before merge by retaining the original executable/API shapes where possible; any Verus-required rewrite needs the original form and concrete reason recorded adjacent to the replacement. No proof/trust, contract, invariant, rlimit, or reusable external-spec defect was established from the static evidence.

## High

No findings.

## Medium

### Preserve the executable and public API shapes

- **Guideline:** `preserve-exec-code`
- **Locations:** `lock-protocol/src/exec/rw/cursor.rs:44`, `lock-protocol/src/exec/rw/mem_content/meta_slot/mod.rs:89`, `lock-protocol/src/exec/rw/mem_content/meta_slot/mod.rs:123`, `lock-protocol/src/exec/rw/node/mod.rs:22`, `lock-protocol/src/mm/page_table/cursor/mod.rs:77`
- **Evidence:** The patch changes `pub path: Vec<GuardInPath>` to `pub path: [GuardInPath; MAX_NR_LEVELS]`, `pub vec: Vec<PPtr<MetaSlot>>` to `pub vec: Vec<* const MetaSlot>`, and `pub ptr: PPtr<MetaSlot>` to `pub ptr: *const MetaSlot`. It also changes `const MAX_NR_LEVELS: usize = 4` to `pub const MAX_NR_LEVELS: usize = 4`; the only new consumer shown by the patch is the internal import `use crate::mm::page_table::cursor::MAX_NR_LEVELS` in `src/exec/rw/cursor.rs:22`. None of the replacements has an adjacent `Origin Rust:` block or a concrete explanation of the Verus constraint that requires it.
- **Problem:** These are executable representation and caller-facing type changes, plus a visibility widening made to support the proof-side conversion. The guideline requires executable changes to remain minimal, preserve upstream API shapes, and retain the original form with the concrete reason when Verus truly requires a rewrite; it explicitly rejects widening visibility merely to isolate verification.
- **Suggestion:** Keep the original `Vec`/`PPtr` field shapes and adapt the proof locally if Verus supports that route. If a representation conversion is genuinely required, preserve each original declaration in a concise adjacent `Origin Rust:` block, state the specific Verus limitation and demonstrate runtime equivalence; make `MAX_NR_LEVELS` no wider than `pub(crate)` (or duplicate a proof-local constant with an explicit equivalence lemma) rather than adding it to the public API.

## Low

No findings.

## Evidence check record

- Read all 161 lines of `diff.patch`; treated it as the immutable and authoritative change set.
- Compared every changed hunk against the corresponding `before/` and `after/` files and inspected surrounding declarations and contracts.
- Checked the changed raw-pointer relationship statically: `MetaSlotPerm::relate` equates `PointsTo::ptr()` with the stored raw pointer, and `PageTableNode::wf` requires that relationship before `ptr_ref` is used. This did not support a proof/trust or API-contract finding.
- Checked the patch for changed `#[verifier::rlimit(...)]` attributes and newly added or materially changed `std`/`core`/`alloc` external specifications; none were present, so the two workflow checks were not triggered.
- No history analysis, exhaustive rule enumeration, caller experiment, Verus invocation, or CI verification was performed, per the fast-review override. Conclusions are static-review conclusions only.
