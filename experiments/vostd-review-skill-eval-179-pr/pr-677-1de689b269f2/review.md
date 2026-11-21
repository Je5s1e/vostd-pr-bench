# Review: PR 677 snapshot `1de689b269f2` (`diff.patch`)

> Produced from the VOSTD coding guidelines and the skill's API-contract criteria.
> Scope: fast, non-exhaustive isolated review of `diff.patch` (SHA-256 `dc17feea3b7a54ea10231df3607a623dc5ad5154ddb7feaf32ac6b90ff4adff4`) against the supplied `before/` and `after/` trees; the only changed source file is `ostd/src/mm/tlb.rs`.

**Bottom line:** The proof removes several trust annotations, but it also adds a runtime clone to each TLB-enqueue call solely to accommodate ghost ownership. VOSTD's `preserve-exec-code` rule explicitly rejects adding runtime clones merely to ease a proof, so this should be corrected before merge. No high-severity contract, invariant, trust-boundary, rlimit, or reusable-spec issue was established in this fast static pass.

## High

None.

## Medium

### Proof ownership adds runtime cloning to both enqueue paths

- **Guideline:** `preserve-exec-code`
- **Location:** `ostd/src/mm/tlb.rs:80` and `ostd/src/mm/tlb.rs:110`
- **Evidence:** The original bodies forwarded ownership directly: `self.ops_stack.push(op, None);` and `self.ops_stack.push(op, Some(drop_after_flush));`. The new bodies instead say `let op_clone = op.clone();`, consume `op` in `model.tracked_issue_tlb_flush(op);`, and enqueue `op_clone`. The adjacent comment confirms the clone is proof-driven: “The proof consumes `op` ... so `push` records a clone.” The proof helper's signature is `pub proof fn tracked_issue_tlb_flush(tracked &mut self, tracked op: TlbFlushOp)` (`ostd/specs/mm/tlb.rs:111`).
- **Problem:** Both public enqueue operations now execute a clone that was absent before, solely because the proof helper takes the operation as a consuming tracked argument. This directly conflicts with `preserve-exec-code`, which requires proof work to preserve executable Rust and specifically says not to “add runtime clones ... merely to ease a proof.”
- **Suggestion:** Keep the original executable calls that move `op` directly into `OpsStack::push`, and change the ghost/proof interface so it can record the operation without consuming the runtime value (for example, pass a ghost representation or otherwise derive the tracked update from a non-consuming proof value). Validate the exact Verus mode/signature choice, but do not leave an executable clone on either hot path.

## Low

None.

## Evidence check record

- Read all 182 lines of `diff.patch`, then inspected the complete supplied `after/ostd/src/mm/tlb.rs` and the corresponding `before/ostd/src/mm/tlb.rs` around every changed hunk.
- Checked `TlbModel::inv`, `issue_tlb_flush`, and `tracked_issue_tlb_flush` in `after/ostd/specs/mm/tlb.rs`, plus repository call sites in `vm_space.rs` and `mm/test.rs`, to test the new precondition and model-update premise. The added `old(model).inv()` precondition matches the proof helper and the visible verified callers' surrounding invariant discipline; this static pass did not establish an API-contract defect.
- The `Range::len()` replacement was compared with the stated `saturating_sub` semantics and retained as behavior-preserving static evidence; no independent finding was raised.
- `diff.patch` contains no added or changed `#[verifier::rlimit(...)]`, so the `> 200` workflow check did not trigger. It also introduces no external specification for a `std`, `core`, or `alloc` API, so the upstream-reuse workflow check did not trigger.
- Searches found no newly introduced `assume`, `admit`, axiom, or external specification in the reviewed diff. The change removes `external_body` from five functions; remaining trust annotations are unchanged context.
- No Verus verification, history inspection, exhaustive guideline checklist, caller experiment, build, or test was run, as required by the fast-review scope. Conclusions are therefore based only on the supplied patch and before/after source context.
