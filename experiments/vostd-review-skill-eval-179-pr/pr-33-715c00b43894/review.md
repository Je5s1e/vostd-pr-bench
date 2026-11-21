# Review: PR 33 isolated patch snapshot

> Fast, non-exhaustive VOSTD review of `diff.patch` with the supplied `before/` and `after/` trees as context.
> Scope: `pr-33-715c00b43894/diff.patch`; no commit history, caller experiments, Verus run, or exhaustive guideline pass was performed.

**Bottom line:** The patch removes a real executable guard for `INVALID_PADDR` and replaces it with an admitted proof assertion. Because that assertion is erased at runtime, the invalid-address case now continues into address conversion, allocator lookup, and an unsafe union-field dereference. The newly enabled module also exposes a large admitted/trusted proof surface, so its contracts do not yet provide meaningful assurance.

## High

### The invalid-address case now reaches unsafe frame access

- **Guideline:** `preserve-exec-code`
- **Location:** `lock-protocol/src/test/rw_version/exec/cursor.rs:527`
- **Evidence:** Before the patch, lines 507–509 were executable control flow: `if pa == INVALID_PADDR { continue; }`. After the patch, this is `assert(pa != INVALID_PADDR) by { admit(); };`, followed by `allocator.get_pt_frame_from_pa(pa)` at line 534 and `unsafe { frame.page_table_frame.deref() }` at line 535.
- **Problem:** An admitted `assert` is proof-only and cannot replace the removed runtime branch. When the atomic load returns `INVALID_PADDR`, execution no longer retries; it instead treats the sentinel as a valid physical address and proceeds to indexing and unsafe dereference. This is a concrete behavior and safety regression, not merely proof debt.
- **Suggestion:** Restore the executable `if pa == INVALID_PADDR { continue; }` path (or implement another explicit runtime retry/error path). Prove the subsequent validity facts only on the non-sentinel branch; do not use `admit()` to erase a reachable runtime case.

## Medium

### Enabling `rw_version::exec` makes admitted facts part of the active verification boundary

- **Guideline:** `centralize-trusted-boundaries`
- **Locations:** `lock-protocol/src/test/rw_version/mod.rs:1`; `lock-protocol/src/test/rw_version/exec/cursor.rs:213`; `lock-protocol/src/helpers/bits.rs:6`
- **Evidence:** The patch changes the previously commented `// pub mod exec;` to `pub mod exec;`. In that now-active module it adds `assert(tree_path.len() < 3) by { admit(); };` at `cursor.rs:213`, adds further admitted facts at lines 457–458, 527, 624, 638–642, and 650–654, and retains many other admits. It also adds a generally visible helper annotated `#[verifier::external_body]` whose contract asserts `res == low_bits_mask(k as nat)`.
- **Problem:** Activating this module turns its admits into dependencies of public verified APIs such as `lock_range`, while the new bit-mask helper introduces another trusted fact in a general `helpers` module. These assumptions are scattered through caller code rather than confined to a reviewed external/trust boundary, so successful verification would overstate what has actually been proved.
- **Suggestion:** Keep the executable module disabled until the newly relied-on facts are proved, or explicitly isolate the unfinished prototype. Replace local admits with lemmas derived from the model invariants. If the bit-mask bridge truly cannot be verified directly or reused, move the minimal external specification into the project’s centralized external-spec boundary and document the exact tool limitation; otherwise prove the implementation and remove `external_body`.

## Low

No evidence-backed low-severity findings in this fast pass.

## Evidence check record

- Read the complete supplied `diff.patch` and compared the relevant before/after source around the changed physical-address branch and module activation.
- Static trust scan found no added or changed `#[verifier::rlimit(...)]`; therefore there is no `rlimit > 200` finding.
- Static name/signature search found use of VSTD's existing `low_bits_mask` model but no exact `low_bits_mask_u64` implementation in the available snapshot. The external wrapper remains a trust-boundary issue; this fast pass does not claim that a reusable executable bridge definitely exists.
- The added `ManuallyDrop` import uses the shared `vstd_extra::manually_drop` specification while the duplicate local copy is removed; no spec-reuse finding is warranted there.
- API-contract review found the most important caller-visible issue to be the erased sentinel handling described above. No additional contract finding was retained without verification evidence.
- **No verification disclosure:** Per the requested fast-review override, no Verus invocation, build, test, standalone proof, targeted caller experiment, or history audit was run. Findings are based on static before/after evidence only.
