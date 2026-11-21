# Review: PR 492 captured diff (snapshot e7a37a7d7080)

> Produced from the captured `diff.patch`, with `before/` and `after/` used for surrounding context.
> Scope: four changed files in `pr-492-e7a37a7d7080/diff.patch`; fast static review of maintainability, proof/trust boundaries, assumptions, API contracts, invariants, `rlimit > 200`, and reusable specifications.

**Bottom line:** No high- or medium-severity issue is supported by the captured change. The added quantifier triggers are local proof-stability changes, the changed `unsafe` calls are already enclosed in `unsafe` blocks, and the diff introduces no `rlimit` or external standard-library specification change. One low-severity API-documentation mismatch should be corrected now that `drop_meta_in_place` is explicitly an unsafe Rust function.

## High

None.

## Medium

None.

## Low

| Finding | Guideline | Detail |
|---|---|---|
| The new unsafe API's stated safety precondition is narrower than its verified contract and an existing caller. | `document-verified-apis` | At `ostd/src/mm/frame/meta.rs:881`, the documentation says, “The reference count must be 0,” and at line 885 repeats that the caller must ensure it is `0`. The actual `requires` at line 892 accepts `0 || REF_COUNT_UNIQUE`, and `ostd/src/mm/frame/unique.rs:163-166` invokes the function while documenting “We are the sole owner,” i.e. the unique-frame path. Because this patch changes `drop_meta_in_place` to `unsafe fn` at `ostd/src/mm/frame/meta.rs:908`, that prose is now the Rust safety contract and incorrectly makes the supported `REF_COUNT_UNIQUE` call appear invalid. Update both safety bullets to permit `0` **or** `REF_COUNT_UNIQUE`, and explain that either state establishes sole ownership/no concurrent metadata access. |

## Evidence check record

- Read the complete captured `diff.patch` and inspected the corresponding `before/` and `after/` context for every changed hunk.
- Checked all `write_meta` and `drop_meta_in_place` call sites in the captured `after/` tree. Each affected call is already within an `unsafe` block; no missing unsafe boundary was found.
- Compared `drop_meta_in_place` documentation, its `verus_spec` precondition, and its unique-frame caller. The quoted `0`-only prose conflicts directly with the `0 || REF_COUNT_UNIQUE` contract and the existing unique-owner call.
- The added `Ghost::assume_new()` is confined to `#[cfg(any(not(verus_keep_ghost), doc))]` initialization of a field newly declared `ghost`; the captured evidence does not support claiming that it weakens the verified invariant.
- Searched the diff for `#[verifier::rlimit(...)]`; none was added or changed, so there is no `rlimit > 200` finding.
- No new or materially changed external specification for a `std`, `core`, or `alloc` API appears in the diff.
- No Verus run, build, test, history inspection, caller experiment, or exhaustive guideline checklist was performed, per the fast-review override. Conclusions are static and limited to the supplied snapshot.
