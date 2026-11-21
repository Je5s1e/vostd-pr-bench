# Review: PR 612 (`diff.patch`)

> Fast isolated review against the VOSTD maintainability, proof-engineering, workflow, and API-contract criteria.
> Scope: the authoritative `diff.patch` (3 files, 59 insertions and 34 deletions), with `before/` and `after/` used only for source context.

**Bottom line:** The patch replaces `item_roundtrip` axioms with proof bodies, but those proofs are enabled by newly strengthened public axioms that assert the caller-supplied paging level is `1` without requiring it. Because `PagingLevel` is `u8`, this makes the trusted specification inconsistent for any safe slot and non-`1` level. This is a proof-soundness blocker and should be fixed before merge by expressing and requiring the actual reconstruction-validity conditions instead of deriving them from unconstrained inputs.

## High

### The strengthened reconstruction axioms can prove an arbitrary input level equals `1`

- **Guidelines:** `minimize-trusted-surface`, `api-preconditions`
- **Locations:** `ostd/src/mm/kspace/mod.rs:470`, `ostd/src/mm/vm_space.rs:1743`, supported by `ostd/src/mm/page_table/mod.rs:326`
- **Quoted evidence:**

  ```rust
  pub axiom fn item_from_raw_spec_tracked_ptr(pa: Paddr, level: PagingLevel, prop: PageProperty)
      requires
          has_safe_slot(pa),
          prop.flags.contains(crate::mm::page_prop::PageFlags::AVAIL1()),
      ensures
          match KernelPtConfig::item_from_raw_spec(pa, level, prop) {
              MappedItem::Tracked(frame, prop_actual) => {
                  &&& frame.ptr.addr() == crate::mm::frame::meta::mapping::frame_to_meta(pa)
                  &&& level == 1
                  &&& prop_actual == prop
              },
  ```

  and:

  ```rust
  pub axiom fn item_from_raw_spec_frame_ptr(pa: Paddr, level: PagingLevel, prop: PageProperty)
      requires
          has_safe_slot(pa),
      ensures
          UserPtConfig::item_from_raw_spec(pa, level, prop).frame.ptr.addr()
              == crate::mm::frame::meta::mapping::frame_to_meta(pa),
          level == 1,
          UserPtConfig::item_from_raw_spec(pa, level, prop).prop == prop,
  ```

  The trait lemma only requires a safe slot and equality with `item_from_raw_spec`:

  ```rust
  proof fn item_roundtrip(item: Self::Item, paddr: Paddr, level: PagingLevel, prop: PageProperty)
      requires
          has_safe_slot(paddr),
          Self::item_from_raw_spec(paddr, level, prop) == item,
  ```

- **Problem:** `level` is an input to both axioms, yet their preconditions do not constrain it. Calling either axiom with a safe address and `level == 2` yields `2 == 1`; the kernel version additionally needs an `AVAIL1` property, but still has no level constraint. The new `item_roundtrip` proofs therefore move the round-trip claim onto an unsound trusted premise rather than establishing it, and the unsafe `item_from_raw`/trait contract does not formally require the level compatibility described only in prose.
- **Suggestion:** Introduce a formal reconstruction-validity predicate (at minimum capturing `level == 1` for user frames and for kernel tracked frames, plus the applicable flag/ownership conditions), require it on `item_from_raw`, `item_roundtrip`, and the helper axioms, and make both call sites establish it from their page-table invariants. Keep `level == 1` as a precondition or as a property of the reconstructed item's modeled level—not as an unconditional postcondition about an arbitrary argument.

## Medium

No evidence-backed medium-severity findings.

## Low

No useful low-severity findings.

## Evidence check record

- Read the complete authoritative patch and inspected the corresponding before/after trait, implementation, helper-axiom, and two cursor call-site contexts.
- Checked all changed `item_roundtrip` and strengthened helper contracts. `PagingLevel` is defined as `u8`, so values other than `1` are admitted by the type; neither strengthened axiom requires `level == 1`.
- The two occurrences of `C::item_roundtrip` are existing callers outside the patch. Their surrounding invariants may establish a valid level in those particular paths, but that does not repair the public axioms or trait contract, which remain callable under the weaker written preconditions.
- No added or modified `#[verifier::rlimit(...)]` appears in the patch, and no new or materially changed external specification for a `std`, `core`, or `alloc` API appears, so the two workflow checks do not produce findings.
- Per the requested fast-review override, no Git history, Verus run, caller experiment, or exhaustive checklist was performed. Findings are based on static contract analysis only; CI/Verus verification was not independently rerun.
