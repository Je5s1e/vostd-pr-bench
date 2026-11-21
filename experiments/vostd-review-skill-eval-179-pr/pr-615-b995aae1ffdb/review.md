# Review: PR 615 snapshot `b995aae1ffdb` (fast static review)

## Scope and bottom line

Reviewed the complete authoritative `diff.patch` against the supplied before/after snapshots, limited to maintainability, proof/trust boundaries, assumptions, API contracts, invariants, rlimit changes above 200, and reusable specifications.

The change is directionally sound: it removes two constructor axioms from the trusted base and implements the constructors as ordinary proof functions. The deleted invariant proof blocks do not change the stated contracts. One low-severity maintainability/API-surface issue remains. No high- or medium-severity findings were identified by static inspection.

**Bottom line:** No high- or medium-severity issue was found; one low-severity maintainability/API-surface issue remains.

## High

None.

## Medium

None.

## Low

### The new tracked constructors are single-use public helpers with the wrong proof-role name

**Location:** `ostd/specs/mm/vm_space_embedding.rs:405-416`, `433-444` (call sites at `496` and `661`)

**Rules:** `inline-single-use-proof-helpers`, `name-proof-roles`

`lemma_cursor_entry_new` and `lemma_vm_io_entry_new` each have exactly one caller in this module, and the repository snapshot contains no other caller of either new name. Their bodies are only struct literals, so they do not isolate a substantial proof or establish a reusable mathematical fact. Making them `pub` expands the proof API without an evidenced external consumer. Moreover, these functions construct and return tracked resources; the naming guideline reserves `lemma_` for proved reusable facts and calls for `tracked_` on helpers that manipulate tracked variables.

Inline the struct literals at their respective call sites if Verus accepts that form. If a named constructor remains necessary as a language or proof-context boundary, make it private and name it `tracked_cursor_entry_new` / `tracked_vm_io_entry_new` (and document the constraint if it is non-obvious). This also avoids replacing two public `axiom_*` symbols with differently named public symbols when the only evidenced consumers are internal.

## Evidence check record

- Read all 169 lines of `diff.patch` and checked every changed hunk against the corresponding before/after file.
- Confirmed that `lemma_cursor_entry_new` and `lemma_vm_io_entry_new` each have one call site in the changed module and no other call sites under the supplied `after` snapshot.
- Confirmed the constructors now have concrete bodies (`CursorEntry { ... }` and `VmIoEntry { ... }`), so the two former axioms are removed from the trust boundary rather than merely renamed.
- Re-read `VmStore::inv` and the contracts of all four functions whose explicit invariant assertions were deleted. The patch does not weaken their `requires old(s).inv()` / `ensures final(s).inv()` contracts; the removals are proof-scaffolding changes, not contract changes.
- No `assume`, `admit`, new axiom, external specification, or `#[verifier::rlimit(...)]` change appears in the patch. Therefore there is no rlimit-over-200 or upstreamable external-spec finding.
- Checked similarly named constructor axioms elsewhere in the snapshot; they have different signatures and live in the separate `ostd::specs::mm::embedding` module, so they do not refute the single-use result for the two changed functions.

## Verification disclosure

Per the fast-review constraint, I did not run Verus, compile the repository, inspect Git history, execute caller experiments, or perform the skill's exhaustive persona/checklist workflow. Conclusions are based on static inspection of the authoritative patch and supplied before/after context only.
