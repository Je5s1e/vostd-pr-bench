# Review: PR 857 captured patch `51bb973322ec`

> Fast, non-exhaustive VOSTD review of `diff.patch`, with the captured `before/` and `after/` trees used only for local context.
> Scope: `pr-857-51bb973322ec/diff.patch` (69 lines), changing `ostd/specs/mm/frame/linked_list/linked_list_owners.rs`, `ostd/src/mm/vm_space.rs`, and `ostd/src/sync/wait.rs`.

**Bottom line:** The linked-list proof and overflow-safe bound rewrite remove local trust without revealing a static contract or invariant regression. The wait-loop change, however, still discharges the public result contract with an `admit()` after explicitly observing that the available closure fact is about a different `FnMut` state. That remaining trusted bridge should be resolved before this proof is treated as complete.

## High

No evidence-backed high-severity findings in this fast pass.

## Medium

### The successful wait result still depends on an admitted cross-state closure fact

- **Guidelines:** `centralize-trusted-boundaries`, `complete-external-contracts`
- **Location:** `ostd/src/sync/wait.rs:393`
- **Evidence:** The public contract promises `Ok(res) => cond.ensures((), Some(res))` at lines 356-365. In the changed branch, the checked call establishes `assert(cond.ensures((), Some(res)));`, but the new comment then states, “The postcondition talks about the entry-state closure, while `cond` has advanced past this call, so the fact above cannot reach the exit,” immediately followed by `proof! { admit(); }` at lines 390-393. The captured before version already had two admissions in this branch; the patch removes the inner one but retains this second bridge.
- **Problem:** `F` is an arbitrary `FnMut`, so its captured state may change on each call. The checked fact about the post-call closure state does not by itself establish the function's stated fact about the entry-state closure; the admission makes that caller-visible result guarantee trusted rather than verified. This finding is about incomplete trust removal at a materially rewritten boundary, not a claim that the patch newly introduced the admission.
- **Suggestion:** Reformulate the contract so the `Ok` guarantee refers to the successful invocation's modeled closure state (for example, an appropriate final-state/call-result predicate), or add and prove an explicit state-invariance condition on the closure contract if entry-state wording is required. Then discharge the return branch from `r == Some(res)` and the call guarantee and remove the remaining `admit()`; do not centralize this particular fact as an axiom unless its semantic validity for arbitrary `FnMut` closures is independently established.

## Low

No evidence-backed low-severity findings in this fast pass.

## Evidence check record

- Read all 69 lines of `diff.patch` and inspected the corresponding captured before/after regions and enclosing APIs for all three changed files.
- Compared the wait-loop branch directly: the before image contains two admissions in the successful branch, while the after image proves the scrutinee/call fact but retains one admission specifically to connect different closure states.
- Checked `CursorMut::unmap` through its subsequent `end_va = self.virt_addr() + len` use and loop invariant. The two new assertions establish the non-overflowing pass domain before that addition and preserve the documented out-of-range panic domain; no static finding was retained.
- Checked `tracked_destroy_empty` and its call site. The change removes `external_body`/`unimplemented!()` and leaves the same three emptiness preconditions; no new caller-visible assumption or invariant weakening was found statically.
- Static scan of the authoritative patch found no changed `#[verifier::rlimit(...)]` and no newly added or materially changed external specification for a `std`, `core`, or `alloc` API.
- The expected live `docs/coding-guidelines/{README,maintainability,proof-engineering,workflow}.md` files are absent from this isolated workspace root. Guideline IDs were therefore checked against the bundled VOSTD review skill/personas and the available captured maintainability-guideline snapshot; this limits checklist coverage but not the quoted source evidence above.
- **No-verification disclosure:** Per the requested fast-review override, no Verus run, CI run, history inspection, exhaustive rule-by-rule audit, standalone proof experiment, targeted caller experiment, or controlled variant was performed. Verification status is unknown; conclusions are based on static patch and captured-context evidence only.
