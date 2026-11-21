# Review: PR 909 snapshot `diff.patch`

> Produced from the supplied patch and its `before/` and `after/` source snapshots, using the VOSTD maintainability, proof-engineering, API-contract, and narrowly applicable workflow criteria.
> Scope: fast non-exhaustive review of `pr-909-a2d5bf577533/diff.patch`; no repository history, sub-reviewers, Verus runs, caller experiments, or exhaustive checklist pass.

**Bottom line:** The revised `Arc<T>` implementation does not preserve the permission that justifies its borrowed raw-pointer view. It reconstructs an `Arc` without passing the owning permission required by the trusted `arc_from_raw` contract, and later obtains a new owning permission for the same runtime strong reference before converting that permission into a static borrow. This breaks the proof-level ownership story at a trusted boundary and should block merging until the round trip carries the original borrowed permission end to end.

## High

### The `Arc` borrowed round trip discards the input permission and manufactures a replacement

- **Guidelines:** `complete-external-contracts`, `centralize-trusted-boundaries`
- **Location:** `ostd/src/sync/rcu/non_null/mod.rs:454`
- **Evidence:** The trait requires `raw_as_ref` to receive a borrowed reading permission (`Tracked<Self::RefPermission<'a>>`), and the `Arc` implementation defines that permission as `&'a ArcPointsTo<T>` (`mod.rs:393`). The changed implementation destructures it as `Tracked(perm)` but never uses it:

  ```rust
  unsafe fn raw_as_ref<'a>(
      raw: NonNull<Self::Target>,
      Tracked(perm): Tracked<Self::RefPermission<'a>>,
  ) -> Self::Ref<'a> {
      unsafe {
          // TODO: Model borrowed construction; arc_from_raw requires an owning token.
          ArcRef { inner: ManuallyDrop::new(arc_from_raw(raw.as_ptr())), _marker: PhantomData }
      }
  }
  ```

  The called trusted wrapper explicitly requires an owning ghost input (`verified_libs/vstd_extra/src/external/smart_ptr.rs:291-301`):

  ```rust
  with Tracked(points_to): Tracked<ArcPointsTo<T>>,
  requires
      points_to.ptr() == ptr,
      points_to.is_init(),
  ```

  The reverse conversion then calls `arc_into_raw` to obtain a fresh `owned_perm` and immortalizes it as a shared permission (`mod.rs:471-476`):

  ```rust
  proof_decl! { let tracked owned_perm: ArcPointsTo<T>; }
  let ptr = (#[verus_spec(with => Tracked(owned_perm))]
  arc_into_raw(ManuallyDrop::into_inner(ptr_ref.inner))).cast_mut();
  proof_decl! { let tracked perm = tracked_static_ref(owned_perm); }
  ```

- **Problem:** At runtime, `raw_as_ref`/`ref_as_raw` merely borrow and round-trip the single strong reference represented by the original raw pointer. At proof level, however, the changed code stops connecting reconstruction to the original permission and asks the external `arc_into_raw` model for another owning `ArcPointsTo` token for that same runtime reference. Turning the replacement into a static tracked reference does not restore the missing relationship to the caller's original borrow; it leaves two proof resources describing one strong reference and can outlive consumption of the original owner.
- **Suggestion:** Carry the original `&'a ArcPointsTo<T>` inside `ArcRef` as a tracked field and return that exact borrow from `ref_as_raw`, as the `BoxRef` design does. If Verus cannot specify the runtime `Arc::from_raw`/`Arc::into_raw` borrowed round trip directly, add one narrowly scoped trusted wrapper in `vstd_extra::external` whose contract takes and returns the same borrowed permission and exposes pointer identity; do not obtain a second owning `ArcPointsTo` token.

## Medium

### A generic alignment fact is strengthened through local axioms instead of the external-model boundary

- **Guideline:** `centralize-trusted-boundaries`
- **Location:** `ostd/src/sync/rcu/non_null/mod.rs:114`
- **Evidence:** The patch strengthens `lemma_align_bits_range` so every implementation must establish `Self::align_bits_inv()` (`mod.rs:114-119`). For `Box<T>` and `Arc<T>`, the new invariant equates an externally defined constant to Verus layout (`mod.rs:229-234`, `395-400`), while the implementations discharge the stronger contract with local axioms (`mod.rs:284-285`, `436-437`):

  ```rust
  #[verifier::external_body]
  const ALIGN_BITS: u32 = core::mem::align_of::<T>().trailing_zeros();

  open spec fn align_bits_inv() -> bool {
      1usize << Self::ALIGN_BITS == vstd::layout::align_of::<T>()
  }

  axiom fn lemma_align_bits_range();
  ```

- **Problem:** The patch replaces caller-local `assume` statements with a reusable fact, but the fact remains trusted twice in an ordinary OSTD implementation. Its truth depends on the external Rust constant and layout model, so keeping duplicate generic axioms here obscures the actual trust boundary and permits the two implementations to drift.
- **Suggestion:** Specify the `align_of::<T>().trailing_zeros()` relationship once in the external specification layer (or reuse an existing vstd layout theorem if available), then prove both trait implementations from that single boundary fact.

## Low

| Finding | Guideline | Detail |
|---|---|---|
| Propose the new `NonNull::eq` model upstream | `upstream-reusable-specs` | `verified_libs/vstd_extra/src/external/nonnull.rs:10-18` adds a generic external specification for a `core` API. Because this model is broadly reusable and otherwise becomes a second long-lived trust source, submit it to Verus/vstd (or document the upstream tracking issue) rather than leaving it only in OSTD's external-spec layer. |

## Evidence check record

- Read the complete supplied `diff.patch`, then checked the relevant `before/` and `after/` definitions of `NonNullPtr`, `ArcRef`, `ArcPointsTo`, `arc_into_raw`, and `arc_from_raw`.
- Confirmed that the old `raw_as_ref` explicitly supplied its `ArcPointsTo` token to `arc_from_raw`, while the new version removes that `#[verus_spec(with perm)]` connection.
- Confirmed that `arc_into_raw`'s external contract returns an owning `ArcPointsTo<T>` and `arc_from_raw`'s external contract consumes one; the changed round trip instead converts the newly returned owner into a static tracked reference.
- Confirmed that no `#[verifier::rlimit(...)]` change appears in the patch, so there is no `rlimit > 200` finding.
- No claim was based on verification output. Per the requested fast-review override, I did not run Verus, compile the tree, inspect history, perform isolated caller experiments, or exhaustively enumerate every guideline rule. Findings are static, evidence-backed review conclusions from the supplied snapshot only.
