# Review: PR #171 snapshot `81a05f39c6ad`

> Produced from the VOSTD coding-guideline criteria and the skill's API-contract criteria.
> Scope: `diff.patch` is authoritative, with `before/` and `after/` used only for line-numbered context. No repository history, Verus run, exhaustive checklist, caller experiment, or CI verification was performed under the fast-review override.

**Bottom line:** The patch introduces a public trusted proof function that can manufacture a linear `free_paddrs` token without connecting it to any allocator fact or even to the address being allocated. It also leaves the changed allocation invariant dependent on an explicit `admit()`. Both issues cross the proof trust boundary and should be resolved before merge.

## High

### The new helper can mint arbitrary free-address authority

- **Guidelines:** `centralize-trusted-boundaries`, `complete-external-contracts`, `api-postconditions`
- **Location:** `lock-protocol/src/exec/rcu/node/mod.rs:124`
- **Evidence:**

  ```rust
  // Allocator is trusted so we can assume the paddr is free.
  #[verifier::external_body]
  pub proof fn assume_free_paddr_token(inst: SpecInstance) -> (res: FreePaddrToken)
      ensures
          res.instance_id() == inst.id(),
  ```

  The caller obtains this token at line 185 and passes it to `normal_allocate(nid@, paddr, ..., free_paddr_token)` at lines 187-193. The state-machine transition consumes `set {paddr}` from `free_paddrs` (`lock-protocol/src/spec/rcu/tree.rs:388`), but the helper neither accepts `paddr` nor ensures `res.element() == paddr` (set-sharding tokens expose their represented element). It also has no allocator permission or precondition and is public, so it may be called repeatedly for the same instance.
- **Problem:** Trust in the allocator does not justify an unconstrained token constructor. This boundary can duplicate linear authority and does not state the key fact needed by the consuming transition: that the token represents the particular physical address returned by the allocator.
- **Suggestion:** Move this trust boundary into the allocator's external-spec/boundary module and derive exactly one token from the allocator operation that establishes freshness. At minimum, accept the allocated `paddr` and the relevant allocator evidence and ensure both `res.instance_id() == inst.id()` and `res.element() == paddr`; keep the function non-public unless callers genuinely need this proof authority.

### The changed allocation invariant is still established by `admit()`

- **Guidelines:** `centralize-trusted-boundaries`, `document-real-proof-debt`
- **Location:** `lock-protocol/src/spec/rcu/tree.rs:585`
- **Evidence:**

  ```rust
  assert(post.starys_count_false(node_id) == 1) by {
      // This is absolutely true, but I do not have enough time
      admit();
  }
  ```

  This assertion is used immediately to establish the state-machine invariant `post.starys_count_false(node_id) <= 1` at lines 573-594. The patch changes the projection/count model and replaces the prior proof at this exact obligation with this new admitted assertion.
- **Problem:** The inductiveness of the changed invariant is trusted rather than proved. The accompanying comment is not evidence and explicitly records scheduling pressure instead of the missing logical obligation, so reviewers cannot assess or maintain the proof.
- **Suggestion:** Prove that projecting `post.strays`, after inserting `(nid, paddr) => false`, yields exactly the previous projection with `paddr => false`, then use the already established zero pre-count to derive a post-count of one. If the proof cannot be completed in this PR, do not claim the invariant as verified; isolate and document the precise missing lemma rather than admitting the result inline.

## Medium

No evidence-backed medium-severity findings.

## Low

No useful low-severity findings.

## Evidence check record

- Read all 1,308 lines of `diff.patch`; treated it as the immutable review input.
- Used the corresponding `after/` files to resolve the reported source line numbers and the `before/` files to confirm that the cited lines are introduced or materially changed by this patch.
- Checked the new `free_paddrs` field, initialization, allocation consumption, invariant, exported token alias, and sole new executable caller together. The helper's contract contains only the instance-id clause; there is no address/element clause or allocator evidence elsewhere in the snapshot.
- Checked every added/removed occurrence of `admit`, `assume`, `external_body`, and `rlimit` in the patch. The report includes the new trusted helper and the materially rewritten allocation obligation; unchanged pre-existing admits were not reported independently.
- No `#[verifier::rlimit(...)]` change appears in scope, so the `> 200` workflow check did not trigger. No new or materially changed external specification for a `std`, `core`, or `alloc` API appears in scope, so the upstream-spec workflow check did not trigger.
- Static refutation did not find a contract clause tying `FreePaddrToken::element()` to the allocation address, or a checked proof replacing the cited `admit()`.
- **No-verification disclosure:** Per the fast-review override, no Verus invocation, build, CI run, history inspection, or isolated caller experiment was performed. Findings are based solely on the authoritative patch and supplied before/after context.
