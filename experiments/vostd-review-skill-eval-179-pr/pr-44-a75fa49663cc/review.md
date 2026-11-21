# Review: PR #44 authoritative diff (static fast review)

> Produced from the VOSTD coding guidelines and API-contract criteria.
> Scope: `pr-44-a75fa49663cc/diff.patch`, with `before/` and `after/` used only as surrounding context. The patch promotes the RW lock-protocol implementation from `src/test/rw_version` into production modules and adds executable tree helpers.

**Bottom line:** The new executable node helper has a trusted contract that its implementation directly contradicts: it always returns an empty trace, so every non-root valid node is reported at depth zero. A second merge-blocking concern is the promotion of the main allocation/range-lock path behind local `external_body` annotations, making strong state-transition guarantees trusted rather than verified. No `rlimit` above 200 or changed `rlimit` annotation appears in the authoritative patch.

## High

### `nid_to_trace_exec` promises the spec trace but always returns an empty vector

- **Guidelines:** `complete-external-contracts`, `centralize-trusted-boundaries`
- **Location:** `lock-protocol/src/exec/rw/utils.rs:44`
- **Evidence:** The new function is marked `#[verifier::external_body]`, promises `Self::exec_trace_to_ghost(res) =~= NodeHelper::nid_to_trace(nid as NodeId)`, but its complete body is `Vec::new()` (`utils.rs:44-52`). The referenced model returns an empty trace only for the root and otherwise calls `nid_to_trace_rec` (`lock-protocol/src/spec/utils.rs:205-214`). The verified wrapper `nid_to_dep_exec` then returns `trace.len()` (`exec/rw/utils.rs:54-62`), so every legal non-root input executes with depth `0` while its postcondition claims the modeled nonzero depth.
- **Problem:** This is not merely unfinished proof work: the trusted postcondition is false of the executable body. `get_child_exec` consumes the false depth to select a subtree size, so the mismatch can also compute the wrong child ID for non-root nodes while downstream proofs are allowed to assume the specified result.
- **Suggestion:** Implement the actual node-to-trace conversion and verify it, or remove these executable wrappers until that implementation exists. Do not retain `external_body` on a placeholder body with a functional-correctness postcondition.

### Production allocation and range locking are promoted with their state transitions wholly trusted

- **Guidelines:** `centralize-trusted-boundaries`, `document-real-proof-debt`
- **Locations:** `lock-protocol/src/exec/rw/cursor.rs:274`, `lock-protocol/src/exec/rw/cursor.rs:409`
- **Evidence:** `TransHandler::allocate` is newly annotated `#[verifier::external_body]` and still contains the unresolved exclusivity assertion `assert(prev == INVALID_PADDR) by { admit(); }` (`cursor.rs:274-309`). The public `lock_range` entry point is also newly annotated `#[verifier::external_body]` while advertising strong guarantees including `res.0.wf()`, `res.0.init_wf(*va)`, and a returned model in `WriteLocked` state (`cursor.rs:409-429`). Its body contains multiple admitted facts, including replacing the previous `if pa == INVALID_PADDR { continue; }` behavior with `assert(pa != INVALID_PADDR) by { admit(); }` in the patch.
- **Problem:** The change moves this code out of a test-only module and exposes a production path whose central allocation, exclusivity, termination, and lock-state claims are accepted as axioms at the caller boundary. The trust is distributed in ordinary exec code rather than isolated in a narrowly audited external-specification layer, and the patch provides no safety/trust-boundary statement explaining what establishes the admitted exclusivity and allocation assumptions.
- **Suggestion:** Keep the implementation test-only until these bodies verify, or reduce and isolate the unavoidable trusted primitive behind a narrowly contracted external module. Verify `allocate` and `lock_range` against that primitive, and explicitly document the remaining trusted assumption and why it is sound before promoting the API.

## Medium

### `get_child_exec` omits the offset bound required by both its model and implementation

- **Guidelines:** `complete-external-contracts`, `api-preconditions`
- **Location:** `lock-protocol/src/exec/rw/utils.rs:64`
- **Evidence:** The public executable helper requires only a valid non-leaf `nid` (`utils.rs:66-68`), but its body immediately trusts `assert(0 <= offset < 512) by { admit(); }` and computes `nid + offset * sz + 1` (`utils.rs:80-82`). The modeled `NodeHelper::get_child` explicitly recommends `0 <= offset < 512` (`spec/utils.rs:266-273`). Since `offset` is `u64`, `0 <= offset` is automatic, but no caller-visible condition excludes `offset >= 512` or arithmetic overflow.
- **Problem:** Any public caller may satisfy the declared preconditions with, for example, `offset == 512` or `u64::MAX`; the implementation's hidden assumption is then false, and its trusted validity/subtree postconditions are unsupported. This is a contract hole rather than a caller restriction: the body itself requires the bound for its documented child-offset model.
- **Suggestion:** Add `offset < 512` (and any arithmetic non-overflow condition not derivable from the node/tree bounds) to `requires`, then verify the implementation. Alternatively make the API fallible for invalid offsets and specify both outcomes.

## Low

No low-severity findings met the fast-review evidence threshold.

## Evidence check record

- Read `diff.patch` as the authoritative review input and checked the corresponding `before/` and `after/` files for line-numbered context.
- Refuted the possibility that the empty trace is valid for every permitted input by checking `NodeHelper::nid_to_trace`: only `root_id()` takes the empty branch; non-root valid IDs use `nid_to_trace_rec`.
- Checked the suggested offset correction against the modeled signature: `NodeHelper::get_child` itself carries the missing `0 <= offset < 512` recommendation, so adding `offset < 512` preserves rather than strengthens the intended domain.
- Searched the authoritative patch and after-tree for `rlimit`; no changed annotation or value above 200 was found.
- The newly added trusted helpers model project-local logic, not a materially changed external specification for a `std`, `core`, or `alloc` API; no upstream-spec finding applies.
- No Verus run, build, history inspection, isolated caller experiment, or exhaustive checklist was performed, per the requested fast-review override. Findings are based on static source/contract evidence only.
