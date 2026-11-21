# Review: PR #906 snapshot f6e33f374ccc

> Fast isolated VOSTD review using `diff.patch` as the authoritative change set, with the supplied `before/` and `after/` trees only for context.
>
> Scope: four changed paths: `ostd/src/task/kernel_stack.rs`, `ostd/src/task/mod.rs`, `ostd/src/task/stack_size.rs`, and `tools/tests/stack_size.rs`.

**Bottom line:** The new parser contract is coherent with the preserved executable behavior, and the patch adds no high-severity proof or API-contract defect. However, the patch restructures executable Rust solely to isolate verification in exactly the way the VOSTD `preserve-exec-code` rule forbids. Restore the parser in place before merge rather than introducing a sibling module and widened visibility for the proof harness.

## High

None.

## Medium

### Keep the parser in its original module

- **Guideline:** `preserve-exec-code`
- **Location:** `ostd/src/task/stack_size.rs:34` (with scope evidence at `ostd/src/task/mod.rs:10` and `ostd/src/task/kernel_stack.rs:99`)
- **Evidence:** The patch adds `mod stack_size;`, changes the original private wrapper into `pub(super) const fn parse_u32_or_default`, and leaves a narrated commented copy in `kernel_stack.rs`: “Moved to the private stack_size module so the parser can be verified while the rest of kernel_stack is disabled” and “The wrapper becomes pub(super) inside the private sibling module”. The authoritative guideline says that when target code is commented out, verification should “enable it in place” and must not “extract a new module, widen visibility, or change call paths merely to isolate verification.” It also says unchanged disabled code should be wrapped directly without an `Origin Rust:` label or repeated status narration.
- **Problem:** This is not a proof-only change: it moves executable functions to a new module, widens one function from private to `pub(super)`, and changes the production call path specifically for verifier isolation. That creates avoidable runtime-code churn and a second, narrated copy of the original implementation for reviewers to reconcile.
- **Suggestion:** Restore both parser functions at their original location and visibility in `kernel_stack.rs`. Enable only the target code and necessary dependencies in place for verification; if the current isolated test cannot import that source without restructuring production code, adjust or defer the harness rather than moving the executable implementation. Remove the explanatory duplicate/`Origin Rust:` block once the original functions are restored.

## Low

None.

## Evidence check record

- Read the complete 167-line authoritative patch and inspected the corresponding before/after definitions and call sites.
- Confirmed that `parse_u32_or_default` preserves the former executable bodies and that its contract distinguishes `Some(value)` from `None`: only `Some` requires `valid_decimal`, while `None` returns `default`.
- Checked the loop invariant and local recursive prefix lemma statically. The digit predicate plus the prefix bound supports the non-underflow/non-overflow obligations; no contrary evidence supports an API-precondition or API-postcondition finding.
- Searched the patch for assumptions, admits, axioms, external specifications, verifier trust annotations, and `rlimit` changes. None are introduced, so there is no `rlimit > 200` or upstream reusable `std`/`core`/`alloc` specification finding.
- No Verus run, build, test, history inspection, exhaustive rule pass, or isolated caller experiment was performed, per the fast-review override. Conclusions are static and limited to the captured patch and supplied context.
