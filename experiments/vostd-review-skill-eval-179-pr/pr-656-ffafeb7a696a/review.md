# Review: PR 656 snapshot ffafeb7a696a

> Fast, non-exhaustive review of the supplied `diff.patch` and its captured before/after context.
> Scope: `pr-656-ffafeb7a696a/diff.patch` (SHA-256 `ed94e8668a0058cda4dacfce3ecd627871882d7e0327840a68e0bc92cd10f227`), changing `ostd/specs/mm/embedding/{cursor.rs,io.rs,mod.rs}`.

**Bottom line:** No strong evidence-backed high-, medium-, or useful low-severity issue was found. The patch reduces the trusted proof surface: it replaces two owner-preservation axioms with reflexive proof lemmas and replaces the cursor-entry constructor axiom with a concrete tracked construction after correctly marking its non-linear fields `ghost`. The changed contracts and their callers remain aligned in the captured after-tree.

## High

None.

## Medium

None.

## Low

None.

## Evidence check record

- **Trust and assumptions:** The diff removes `vm_reader_limit_embedded`, `vm_reader_skip_embedded`, and `axiom_cursor_entry_new` as axioms. Their replacements contain no `assume`, `admit`, `external_body`, or new axiom. At `ostd/specs/mm/embedding/io.rs:155-174`, the reader limit/skip lemmas do not mutate `owner`, so the retained postconditions `final(owner).inv()` and `*final(owner) == *old(owner)` follow from the required `old(owner).inv()`. The same established pattern appears for writer limit/skip at lines 217-234.
- **Tracked/ghost invariant:** At `ostd/specs/mm/embedding/mod.rs:546-552`, the cursor's descriptive fields (`vm_space`, `kind`, and `va`) are now `ghost`, while the linear ownership resources (`owner` and `guards`) remain tracked. This is consistent with the surrounding `VmIoEntry`, `FrameEntry`, `SegmentEntry`, and `UniqueEntry` definitions and with the `avoid-redundant-mode-markers` rule for tracked structs.
- **Constructor contract:** At `ostd/specs/mm/embedding/mod.rs:5371-5387`, `tracked_cursor_entry_new` directly constructs `CursorEntry { vm_space, kind, va, owner, guards }`; each equality in its `ensures` clause is the corresponding field projection. The call sites at `ostd/specs/mm/embedding/cursor.rs:717-724` and `:769-776` preserve the same argument order and the same read-only/mutable kind values as before.
- **API contracts and invariants:** The public proof signatures retain their earlier preconditions and postconditions; only their trusted implementations and names change. The dispatch at `ostd/specs/mm/embedding/io.rs:313-329` calls the renamed reader lemmas and preserves the unchanged `VmIoEntry` fields and invariant. No new caller-visible precondition or weakened postcondition was introduced.
- **Maintainability and spec reuse:** The new names follow `name-proof-roles`: reusable proved facts use `lemma_`, and the helper constructing tracked resources uses `tracked_`. Existing analogous helpers are reused as the local pattern rather than adding a parallel abstraction.
- **Workflow checks:** The patch contains no added or changed `#[verifier::rlimit(...)]`, so there is no limit above 200 to report. It also adds or materially changes no external specification for a `std`, `core`, or `alloc` API.
- **Verification disclosure:** Per the requested fast-review override, no Verus run, isolated caller experiment, CI run, git-history analysis, child-agent pass, or exhaustive guideline checklist was performed. Conclusions are based only on static inspection of the supplied patch and captured before/after source.
