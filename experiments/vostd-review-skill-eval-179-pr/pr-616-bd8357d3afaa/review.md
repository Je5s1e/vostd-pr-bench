# Review: PR 616 snapshot `bd8357d3afaa`

> Produced from the VOSTD coding-guideline criteria and the skill's API-contract criteria.
> Scope: fast, non-exhaustive static review of the changes recorded in `diff.patch`, using `before/` and `after/` only for surrounding context.

**Bottom line:** Removing `external_body` reduces the trusted surface and the public contract remains intact, but the proof rewrites the executable expression into several runtime locals without preserving the original form as required by `preserve-exec-code`. Restore the original executable expression around the proof, or retain the required adjacent `Origin Rust:` record if the rewrite is unavoidable. The proof also has a smaller import-hygiene issue.

## High

No strong high-severity findings in this fast pass.

## Medium

### Proof work rewrites the executable implementation without retaining its original form

- **Guideline:** `preserve-exec-code`
- **Location:** `ostd/src/mm/mod.rs:214`
- **Evidence:** Before the patch, the entire runtime body was `PAGE_SIZE << (nr_subpage_per_huge::<PagingConsts>().ilog2() as usize * (level as usize - 1))`. The patch replaces it with three executable locals—`let index_bits = ...;`, `let level_index = ...;`, and `let shift = ...;`—followed by `let ret = PAGE_SIZE << shift;` and `ret` (`after/ostd/src/mm/mod.rs:214-239`). There is no adjacent `Origin Rust:` block or concrete explanation that Verus required this executable rewrite.
- **Problem:** `preserve-exec-code` requires specifications and proofs to leave executable Rust unchanged; if Verus forces a rewrite, it must be minimal, demonstrate unchanged runtime behavior, and retain the original form for review. Although the new expression appears algebraically equivalent, the patch makes that equivalence a review obligation and does not provide the required provenance.
- **Suggestion:** Keep the original one-line executable expression and arrange the proof-only facts around it. If Verus genuinely requires the locals, add the concise adjacent `Origin Rust:` block and concrete tool limitation required by the guideline, and retain evidence that runtime behavior is unchanged.

## Low

| Finding | Guideline | Detail |
|---|---|---|
| Repeated fully qualified proof calls bypass the file's existing imports | `organize-proof-imports` | At `ostd/src/mm/mod.rs:219-237`, the proof spells out four `vstd::arithmetic::power2::...` calls even though line 5 already imports `vstd::arithmetic::power2::*`, and spells out two calls from `vstd_extra::external::ilog2`. Use the imported power2 lemma names directly and add one explicit import for the two `vstd_extra` lemmas; retain qualification only for genuinely one-off or ambiguous symbols. |

## Evidence check record

- Read `diff.patch` in full and treated it as the authoritative reporting scope. Compared the changed function in `before/ostd/src/mm/mod.rs:196-216` with `after/ostd/src/mm/mod.rs:196-240`, and inspected the surrounding paging-constant contract and imports.
- Checked the public API contract: the precondition `1 <= level <= NR_LEVELS + 1` and all three postconditions are unchanged. The patch removes, rather than adds, an `external_body`, and introduces no `assume`, `admit`, axiom, model, spec function, proof function, or external specification.
- Inspected the paging-constant facts used by the proof and the architecture snapshots: the supported primary `PagingConsts` implementations use a 4096-byte base page, 512 entries, four levels, and 48-bit address width. No strong evidence of a broken invariant, unnecessary API precondition, insufficient postcondition, or unsound new trust assumption was found in this static pass.
- Searched the patch for `#[verifier::rlimit(...)]`; none is added or changed, so the `rlimit > 200` workflow check is not triggered. The patch does not add or materially change an external specification for a `std`, `core`, or `alloc` API, so the upstream-spec workflow check is not triggered.
- Reuse check: the patch introduces no new specification or lemma; it reuses existing paging, power-of-two, shift, and `ilog2` lemmas. No evidence-backed duplicate-spec finding applies.
- The fixture does not contain its own `docs/coding-guidelines/{README,maintainability,proof-engineering,workflow}.md`; the applicable rule text was taken from the review skill/personas and the available captured guideline copy elsewhere in this workspace. This was a deliberately fast, non-exhaustive review.
- **No-verification disclosure:** Per scope, this review used no subagents, repository history, Verus execution, Rust build, CI run, exhaustive rule checklist, or caller experiment. Findings are based on direct `diff.patch` and before/after static evidence and have not been machine-verified.
