# Review: authoritative `diff.patch` with `before/` and `after/` context

> Produced from the VOSTD review skill's maintainability, proof/trust, and API-contract criteria.
> Scope: the 39 paths changed by `diff.patch`; `diff.patch` was treated as authoritative, with `before/` and `after/` used only for surrounding context.

**Bottom line:** The patch introduces a blocking ownership-transfer bug in both `Frame::into_raw` and `From<Frame<M>> for Segment<M>`. Each function places a newly constructed duplicate in `ManuallyDrop`, but leaves the actual input `Frame` alive, so its destructor runs at function exit and decrements the reference count that the returned raw/segment representation claims to retain. This breaks the API postconditions and can lead to premature metadata teardown followed by a second decrement when the raw frame or segment is later reclaimed.

## High

### The consumed `Frame` is still dropped after being converted to a raw owner

- **Guideline:** `api-postconditions`
- **Locations:** `ostd/src/mm/frame/mod.rs:570`, `ostd/src/mm/frame/segment.rs:1209`
- **Quoted evidence:**

  ```rust
  pub(in crate::mm) fn into_raw(self) -> Paddr {
      // ...
      let ptr = self.ptr;
      let tracked frame_permission = self.tracked_perm.get().tracked_unwrap();
      let raw_frame = Self {
          ptr,
          _marker: PhantomData,
          #[cfg(verus_keep_ghost_body)]
          tracked_perm: Tracked(None),
      };
      proof_with!(Tracked(()));
      let _ = ManuallyDrop::new(raw_frame);
      // ...
  }
  ```

  ```rust
  fn from(frame: Frame<M>) -> Self {
      let pa = frame.start_paddr();
      let tracked frame_permission = frame.tracked_perm.get().tracked_unwrap();
      let raw_frame = Frame::<M> {
          ptr: frame.ptr,
          _marker: core::marker::PhantomData,
          #[cfg(verus_keep_ghost_body)]
          tracked_perm: Tracked(None),
      };
      let _ = core::mem::ManuallyDrop::new(raw_frame);
      // ...
  }
  ```

  The pre-patch `into_raw` instead used `ManuallyDrop::new(self)`, which suppressed the destructor of the value actually being consumed.

- **Problem:** `raw_frame` is a separate value containing a copy of the pointer. Forgetting that duplicate does not suppress `Drop` for the `self`/`frame` parameter. In executable builds the tracked permission operations are ghost-only, so the original parameter remains a normal live `Frame`; at function exit `Frame::drop` decrements its slot's reference count and may tear down metadata. This contradicts `into_raw`'s stated `*final(regions) == *old(regions)` postcondition and leaves the returned raw address or `Segment` representing an ownership unit that no longer exists. Later `from_raw`/segment drop can therefore operate on torn-down state or decrement the same ownership unit again.
- **Suggestion:** Put the actual input value into `ManuallyDrop` first, then derive the address and transfer its tracked permission from that wrapper. Do not construct and forget a second `Frame`. If Verus cannot express moving the ghost permission through `ManuallyDrop` directly, add one narrowly scoped, documented helper whose executable action is exactly `ManuallyDrop::new(input)` and whose contract transfers the existing permission without changing `MetaRegionOwners`; use that helper from both conversions.

## Medium

No findings.

## Low

No findings.

## Evidence check record

- Read `diff.patch` as the immutable authority and compared the affected `Frame::into_raw` and `From<Frame<M>> for Segment<M>` implementations with their `before/` versions and adjacent `after/` contracts/destructor code.
- Refutation check: the forgotten value is named `raw_frame`, while the consumed parameters remain distinct bindings. `Frame` has a custom destructor, and the tracked permission extraction is ghost-only; nothing in the executable body suppresses destruction of the original parameter.
- The two locations were consolidated because they have the same root cause and correction.
- Changed verifier limits found in scope are `50`, `120`, and `200`; none exceeds the workflow cap of `200`.
- No newly added or materially changed external specification for a `std`, `core`, or `alloc` API was identified. The `core::mem::ManuallyDrop` use is executable trusted-boundary code, not an upstreamable external specification.
- Per the fast-review override, no Git history analysis, exhaustive rule enumeration, Verus run, caller experiment, CI verification, or other dynamic verification was performed. Findings are based on static inspection only.
