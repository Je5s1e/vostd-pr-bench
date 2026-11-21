# Review: PR 658 snapshot `4f0076d7cb29`

> Fast isolated review of the authoritative `diff.patch`, with `before/` and `after/` used only for surrounding context. The requested fast-review override excluded history, Verus runs, exhaustive rule enumeration, experiments, and sub-reviewers.
> Scope: the 14 paths changed by `pr-658-4f0076d7cb29/diff.patch`; review emphasis was maintainability, proof/trust assumptions, API contracts, invariants, `rlimit > 200`, and specification reuse.

**Bottom line:** The new public `ManuallyDrop::into_inner` can return a state-backed value and its stored token without restoring the state-side obligation that callers removed before constructing the wrapper. For `Frame`, this makes the natural unwrap-and-drop path either unusable or able to consume another live frame's multiset entry, so the accounting protocol described by `TrackDrop` is not preserved. No `rlimit` changes or new/changed standard-library external specifications were present.

## High

### `ManuallyDrop::into_inner` does not restore state-backed drop authority

- **Guideline:** `implement-inv-for-models`; `api-preconditions`; `api-postconditions`
- **Location:** `verified_libs/vstd_extra/src/drop_tracking.rs:95`
- **Quoted evidence:**

  ```rust
  #[verus_spec(res =>
      with
          -> obligation: Tracked<T::Obligation>,
      ensures
          res == self@,
          obligation@ == self.obligation(),
  )]
  pub fn into_inner(self) -> T {
  ```

  A changed concrete constructor path first removes the state entry and then puts a freely minted token in the wrapper (`ostd/src/mm/frame/frame_ref.rs:75-80`):

  ```rust
  regions.tracked_redeem_frame_obligation(from_raw_obl);
  let tracked md_obl = DropObligation::tracked_mint(frame.index());
  ...
  let inner = ManuallyDrop::new(frame);
  ```

  But dropping the extracted `Frame` still requires an outstanding state entry (`ostd/specs/mm/frame/frame_specs.rs:279-280`):

  ```rust
  &&& s.frame_obligations.count(self.index()) > 0
  &&& obl.value() == self.index()
  ```

- **Problem:** `into_inner` returns only the value and wrapper token; it has no `T::State` parameter and therefore cannot recreate the ledger entry removed before `ManuallyDrop::new`. With one frame at an index, the extracted value cannot satisfy its drop contract. With another live frame at the same index, the extracted value can satisfy the count-only precondition by consuming that other frame's entry, leaving the other live value with no obligation. This contradicts the changed trait's stated requirement that state detect lost outstanding obligations and that each drop perform its transition exactly once.
- **Suggestion:** Do not expose this generic `into_inner` contract for state-backed implementations. Add a trait operation that restores/reissues the authoritative state obligation and make extraction take `Tracked<&mut T::State>` and call it, or split ledger-less and state-backed wrappers so extraction is available only where no state restoration is required. For `Frame`, the postcondition must insert the frame's index into `frame_obligations` and return the matching authoritative token before the value can be dropped.

## Medium

No medium-severity findings.

## Low

| Finding | Guideline | Detail |
|---|---|---|
| The `Frame` implementation still says `consume_obligation` is a no-op and the token is merely documentary (`ostd/specs/mm/frame/frame_specs.rs:201-203`), but this patch removes that method and makes `Frame::drop` redeem the multiset entry. | `document-real-proof-debt` | Update the trust-boundary comment to describe the actual split protocol: state redemption occurs explicitly before wrapping and in `Drop::drop`, while the wrapper stores a separate token. The current text sends reviewers to a deleted method and understates the ledger's role. |

## Evidence check record

- Read `diff.patch` as the immutable authoritative change and inspected the corresponding `before/` and `after/` definitions and call sites for `TrackDrop`, `ManuallyDrop`, `DropObligation`, `Frame`, `FrameRef`, frame obligation mint/redeem axioms, page-table call sites, and concrete drop contracts.
- Refutation check for the high finding: `ManuallyDrop::into_inner` has no state input or state postcondition; `Frame::drop_requires` still requires a positive multiset count; and changed construction sites explicitly redeem the state entry before storing a separately minted token. No inspected signature restores the entry during extraction.
- `diff.patch` contains no `#[verifier::rlimit(...)]` change and no newly added or materially changed external specification for a `std`, `core`, or `alloc` API.
- No duplicate-specification finding was supported by the inspected repository context.
- Per the fast-review override, no Verus invocation, build, test, caller experiment, history inspection, or exhaustive guideline pass was performed. Findings are static-contract conclusions only; CI/verification status was not checked.
