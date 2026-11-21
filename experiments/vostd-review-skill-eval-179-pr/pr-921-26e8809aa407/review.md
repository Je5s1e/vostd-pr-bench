# Review: PR 921 snapshot `26e8809aa407` (fast static review)

## Scope and bottom line

Reviewed the complete `diff.patch` (241 lines) and corresponding before/after context for:

- `ostd/src/task/kernel_stack.rs`
- `ostd/src/task/mod.rs`
- `verified_libs/vstd_extra/src/lib.rs`
- `verified_libs/vstd_extra/src/number.rs`

This was the requested fast, non-exhaustive static review, focused on maintainability, proof/trust boundaries, assumptions, API contracts, invariants, rlimit changes above 200, and specification reuse. The decimal parser contracts preserve the executable `Some`/`None` behavior and the new shared decimal model is reused by both parser proofs. One medium contract defect remains: `KERNEL_STACK_SIZE` does not expose its exact relationship to `STACK_SIZE_IN_PAGES`, so verified clients cannot recover the defining behavior of this public value. The patch contains no `#[verifier::rlimit(...)]` change or new external specification for a `std`, `core`, or `alloc` API.

**Bottom line:** One medium contract defect remains because `KERNEL_STACK_SIZE` does not expose its exact defining relationship to `STACK_SIZE_IN_PAGES`.

## High

None.

## Medium

### Preserve the defining relationship in the public static's contract

- **Guideline:** `api-postconditions`
- **Location:** `ostd/src/task/kernel_stack.rs:55`
- **Evidence:** The initializer is exactly `STACK_SIZE_IN_PAGES as usize * PAGE_SIZE` (line 60), but its contract states only `KERNEL_STACK_SIZE <= u32::MAX * PAGE_SIZE` and `KERNEL_STACK_SIZE % PAGE_SIZE == 0` (lines 56-58).
- **Problem:** Those clauses permit any page-aligned value within the bound, independent of `STACK_SIZE_IN_PAGES`. A verified client therefore cannot establish the defining and documented relationship between the configured number of pages and the resulting kernel-stack byte size, even though the implementation computes it exactly.
- **Suggestion:** Add an exact clause such as `KERNEL_STACK_SIZE == STACK_SIZE_IN_PAGES as usize * PAGE_SIZE` to the static's `ensures` (retaining the derived bound/alignment clauses if they are useful to callers).

## Low

| Finding | Guideline | Detail |
| --- | --- | --- |
| Disable unchanged imports with direct block comments | `preserve-exec-code` | At `ostd/src/task/kernel_stack.rs:7-20`, unchanged imports are converted into a series of `//` comments (`// use core::sync::atomic::Ordering;`, `// arch::mm::tlb_flush_addr_range`, and others). The preservation rule calls for wrapping temporarily disabled original text directly in `/* ... */`, with per-item block comments where only part of an import tree stays live. This keeps the original bytes, order, and tree shape immediately reviewable. Replace the line comments with direct block comments while leaving `PAGE_SIZE` active in place. |

## Evidence check record

- Read `.codex/skills/vostd-code-review/SKILL.md` and used the requested fast-review override: no child agents, history analysis, Verus execution, experiments, or exhaustive checklist.
- Read `diff.patch` in full and compared every changed region with line-numbered `before/` and `after/` source context.
- Checked `parse_u32_or_default` and `parse_u32` contracts against their executable bodies. The `Some(value)` precondition supplies digit and `u32`-range facts; the `None` arm remains unconstrained and returns `default` exactly.
- Checked the loop invariant and both decimal lemmas statically. The prefix lemma bounds every processed prefix by the complete valid value, supporting the `u32` arithmetic obligations; no `assume`, `admit`, or axiom is introduced.
- Checked the new `vstd_extra::number` surface and its call sites. `decimal_value`, `valid_decimal`, `lemma_decimal_value_step`, and `lemma_decimal_prefix` all have current uses; the shared model avoids duplicating the parser's decimal semantics locally.
- Checked the new `#[verifier::external_body]` initializer boundary at `ostd/src/task/kernel_stack.rs:41-50`. It has no postcondition that could inject a false environmental fact, and the adjacent rustdoc explicitly states that the environment-dependent initializer is unverified and names the missing validity condition.
- Searched the patch for `#[verifier::rlimit(...)]`; none is added or changed. No external specification for a `std`, `core`, or `alloc` API is added or materially changed.
- The supplied PR snapshot does not contain the repository's complete coding-guideline set, so guideline-version-specific exhaustive validation was not possible. No additional finding was inferred from that omission.

## Verification disclosure

No Verus run, build, test, isolated caller experiment, history inspection, exhaustive guideline pass, or external dependency/source verification was performed, per the requested fast-review constraints. Conclusions are based only on static inspection of the supplied patch and before/after snapshot.
