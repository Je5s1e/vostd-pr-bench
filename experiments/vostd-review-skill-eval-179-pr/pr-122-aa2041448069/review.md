# Review: PR 122 supplied patch (fast static review)

> Scope: `diff.patch` is the authoritative change set; `before/` and `after/` were used only for context and source line numbers. This is a fast, non-exhaustive static review. No Verus run, caller experiment, history fetch, or CI verification was performed.

**Bottom line:** The patch should not merge in its current form. The newly implemented allocation path still relies on an `external_body` whose runtime body is `unimplemented!()` and on several new `admit()` statements for its core safety/invariant obligations. Separately, `normal_unlock` consumes `Locked` rather than the `LockedOutside` state produced by `normal_lock`, so the state-machine API both fails to model the intended lock pair and can release the wrong class of lock.

## High

### The new allocation path is still a trusted, panicking placeholder

- **Guideline:** `preserve-exec-code` / `document-real-proof-debt`
- **Location:** `lock-protocol/src/exec/rcu/node/mod.rs:123`; `lock-protocol/src/exec/rcu/node/entry.rs:155`; `lock-protocol/src/exec/rcu/node/entry.rs:210`; `lock-protocol/src/spec/rcu/tree.rs:275`
- **Quoted evidence:** The new helper is declared `#[verifier::external_body] pub fn alloc(...)` and its entire body is `unimplemented!()` (`node/mod.rs:123-146`). The now-executable `normal_alloc_if_none` calls that helper at `entry.rs:186-192`. Its proof additionally establishes the parent/offset facts, node validity, level relation, and returned guard permission with `admit()` at lines 155-168, 182-183, and 210-212. The new `normal_allocate_inductive` proof is also `{ admit(); }` at `tree.rs:275-276`.
- **Problem:** On the successful allocation branch, ordinary execution reaches `PageTableNode::alloc` and panics; verification meanwhile accepts the allocation contract and the facts needed to connect the new node to the parent solely through trusted holes. This does not complete the former `external_body` allocation API—it moves the runtime placeholder into a new helper while expanding the trusted proof surface around the page-table invariant.
- **Suggestion:** Implement the real allocator body (preserving the intended executable allocation behavior), give its unsafe/trusted boundary a concrete justification, and prove the parent/offset, valid-node, level, guard-permission, and `normal_allocate` inductiveness obligations without `admit()`. Until then, keep the incomplete path clearly isolated rather than presenting `normal_alloc_if_none` as a verified executable implementation.

### `normal_unlock` releases the protocol-lock state instead of the normal-lock state

- **Guideline:** `api-preconditions` / `api-postconditions`
- **Location:** `lock-protocol/src/spec/rcu/tree.rs:206`
- **Quoted evidence:** `normal_lock` removes `NodeState::Free` and adds `NodeState::LockedOutside` at lines 198-203. Immediately below it, `normal_unlock` removes `[ nid => NodeState::Locked ]` and adds `Free` at lines 207-211. The new `SpinGuard::wf` definition likewise states that `in_protocol == false` implies the node token value is `LockedOutside` (`lock-protocol/src/exec/rcu/node/spinlock/mod.rs:255`).
- **Problem:** The generated transition cannot consume the token produced by `normal_lock`, while it can consume a `Locked` token belonging to the lock protocol and turn it into `Free`. That contradicts both the transition names and the newly strengthened guard invariant, and permits proof code to bypass the protocol-specific unlock path.
- **Suggestion:** Change `normal_unlock` to remove `NodeState::LockedOutside`. Then prove its inductiveness and check that the normal lock/unlock wrapper contracts transport that exact token state end to end.

## Medium

No medium-severity findings in this fast pass.

## Low

No low-severity findings in this fast pass.

## Evidence check record

- Read all 756 lines of `diff.patch`; it changes seven Rust/Verus files. The supplied snapshots were consulted only to assign post-change line numbers and inspect immediately surrounding declarations.
- Trust-boundary scan found six added `admit()` sites in executable/support code, one added `normal_allocate_inductive` admit, a renamed pre-existing `protocol_allocate_inductive` admit, and one new `#[verifier::external_body]` allocation helper. The first High finding consolidates the newly introduced allocation-path trust debt rather than enumerating each hole separately.
- Checked the state correspondence among `normal_lock`, `normal_unlock`, `SpinGuard::wf`, and the normal allocation caller. The `Locked`/`LockedOutside` mismatch is explicit in the supplied post-change source.
- No added or changed `#[verifier::rlimit(...)]` was present, so no rlimit above 200 was found. No new or materially changed external specification for a `std`, `core`, or `alloc` API was present.
- No verification was run. Findings are based on static source evidence only; this was intentionally a fast, non-exhaustive review.
