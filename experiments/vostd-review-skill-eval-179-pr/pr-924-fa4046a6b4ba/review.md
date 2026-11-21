# Review: PR 924 snapshot (`diff.patch`)

> Scope: the 1,012-line authoritative `diff.patch`, covering eight changed paths, checked against the supplied `before/` and `after/` trees. This was a fast isolated review limited to maintainability, proof/trust assumptions, API contracts and invariants, specification reuse, and changed `rlimit` values above 200.

**Bottom line:** The verification conversion weakens several executable tests into proofs that check only cursor/result shape and no longer check the bytes or values named by the tests. Separately, the newly extended fallible `read_val`/`write_val` contracts still do not expose their documented success behavior, which is already visible in the converted caller having to discard both results.

## High

No high-severity findings.

## Medium

### M1 — Preserve the value-level assertions when converting the I/O tests

- **Guideline:** `preserve-exec-code`
- **Location:** `ostd/src/mm/test.rs:37`
- **Evidence:** The converted `read_write_u32_infallible` still says `/// Tests reading and writing u32 values in Infallible mode`, but its final checks are only `assert!(r1.is_ok());` and `assert!(r2.is_ok());` at lines 78 and 82. The before-version checked both the backing bytes (`assert_eq!(&buffer[..4], &val1.to_le_bytes()[..]);`) and the round trip (`assert_eq!(val1, read_val1);`). The same loss recurs in `fill_infallible` (after lines 181–187 omit the former `assert_eq!(buffer, vec![0xFF; 8])`), `skip_read_infallible` (after line 222 checks only `copied == 3`, replacing `assert_eq!(read_buffer, [30, 40, 50])`), and `write_val_infallible` (after lines 398–412 omit the former final buffer assertion).
- **Problem:** These edits do not merely add proof scaffolding: they remove the observations that detect incorrect data movement. The resulting functions can verify even if an operation advances the expected number of bytes while copying or producing the wrong value, so their names and comments overstate what is tested.
- **Suggestion:** Keep the original `#[ktest]` bodies and their value assertions executable, and add separate verified proof clients if the current memory model cannot establish those assertions. If a single converted function must serve both roles, first strengthen the underlying byte/value contracts enough to retain the original assertions; do not delete the assertions to make the proof pass.

### M2 — Specify the successful outcome of fallible value I/O

- **Guideline:** `api-postconditions`
- **Location:** `ostd/src/mm/io.rs:1096` and `ostd/src/mm/io.rs:1862`
- **Evidence:** Both materially changed contracts now pin only the undersized case—`old(self).remain_spec() < core::mem::size_of::<T>() ==> r == Err(Error::InvalidArgs)` for `read_val`, and the analogous `avail_spec()` clause for `write_val`—plus rollback on `Err`. Neither contract has an `Ok` arm. This contradicts the existing `write_val` verified-properties text at lines 1850–1853, which promises, “On success, the cursor advances by `size_of::<T>()`.” The natural converted caller demonstrates the gap: `fallible_read_write` assigns `write_result` and `read_result` at `ostd/src/mm/test.rs:432` and `:444` but cannot assert success, cursor movement, or `read_result == Ok(val)`.
- **Problem:** A caller that obtains `Ok` learns no success-state fact from either API; for reads, it also learns nothing about the returned value. The new failure classification is useful but leaves the other result branch—the branch described by the public documentation—formally unspecified.
- **Suggestion:** Add conditional `Ok` postconditions that expose the documented cursor advance and unchanged end/range identity. For `read_val`, also relate the returned `T` to the bytes read through the established `Pod`/memory-view model; for `write_val`, relate the successful write to `new_val` where the fallible memory model supports it. Preserve page-fault nondeterminism: this need not claim that a sufficiently large request must succeed.

## Low

| Finding | Guideline | Detail |
|---|---|---|
| L1 | `organize-proof-imports` | `ostd/src/mm/test.rs:43`, `:169`, `:387`, `:558`, and `:593` repeat `vstd_extra::layout::lemma_primitive_layout()` even though the file already has a grouped `vstd_extra` proof import at line 25. Import `layout::lemma_primitive_layout` there and call it by its short name. |

## Evidence check record

- Read the complete authoritative `diff.patch`, then checked the cited locations against both supplied trees (`before/ostd/src/mm/{io,test}.rs` and `after/ostd/src/mm/{io,test}.rs`).
- Checked the new `VmIoOwner::tracked_shrink_range_front` helper and searched the supplied `after/` verified sources for overlapping shrink/range helpers. Its two concrete callers and its preserved invariant/view clauses did not provide strong evidence for a reuse or invariant finding.
- Searched the patch for `#[verifier::rlimit(...)]`; no added or changed rlimit was present, so there is no `> 200` finding.
- The patch adds no new `assume`, `admit`, or `external_body`. The slice/kernel axioms used by the changed constructors predate this patch; the added clauses expose their conclusions but did not establish a new contradiction in this limited review.
- **No-verification disclosure:** Per the fast-review constraint, I did not inspect Git history, run Verus or CI, perform caller experiments, or execute an exhaustive rule-by-rule audit. Findings are based on static diff and before/after source evidence only.
