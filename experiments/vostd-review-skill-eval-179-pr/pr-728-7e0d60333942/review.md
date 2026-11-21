# Review: PR 728 isolated patch

> Scope: `diff.patch` was treated as the authoritative change set, with `before/` and `after/` used only for surrounding context. The patch changes `Cargo.lock` and `ostd/src/util/range_alloc.rs`.
>
> No Verus verification, tests, history inspection, or caller experiments were run, per the requested fast-review constraints.

**Bottom line:** The new resource invariant removes the local `assume`, but it verifies only that every freelist entry is within the allocator's outer bounds. It does not model the allocator's essential ownership property: free ranges are disjoint, successful allocations remove exclusive ranges, and `free` returns only a range owned by the caller. The new persistent initialization token is unrelated to any allocation or range, so the public contract permits double-free and freeing arbitrary in-bounds ranges while still satisfying every proved invariant; this should block merging the verification change until the abstract state and contracts capture allocation ownership.

## High

### The verified invariant and token do not protect allocation ownership

- **Guidelines:** `api-preconditions`, `api-postconditions`, `implement-inv-for-models`
- **Location:** `ostd/src/util/range_alloc.rs:44`, `ostd/src/util/range_alloc.rs:179`, `ostd/src/util/range_alloc.rs:285`, `ostd/src/util/range_alloc.rs:374`
- **Quoted evidence:**

  ```rust
  closed spec fn freelist_wf(fullrange: Range<int>, freelist: Map<usize, FreeRange>) -> bool {
      forall|key: usize| #[trigger]
          freelist.contains_key(key) ==> {
              let block = freelist[key].block;
              &&& fullrange.start <= block.start <= block.end <= fullrange.end
          }
  }
  ```

  ```rust
  // alloc_specific
  ensures
      res is Ok ==> (self@.start <= allocate_range.start
          && allocate_range.end <= self@.end),
      initialized@.id() == self.initialized_id(),
      initialized@@ == (),
  ```

  ```rust
  // free
  requires
      self@.start <= range.start <= range.end <= self@.end,
      initialized is Some ==> initialized->0.id() == self.initialized_id(),
      initialized is Some ==> initialized->0@ == (),
      initialized is None ==> may_panic(),
  ```

  `GhostPersistentSingleton<()>` is duplicated in `get_freelist_guard` at lines 523-529, and neither the witness nor `freelist_wf` mentions an allocated range.
- **Problem:** A successful allocation's only state-related output is a duplicable proof that the freelist has been initialized. Any such witness can therefore be reused to call `free` on any in-bounds range, including the same range twice or a range that was never allocated. The invariant still holds because it requires only outer bounds; it does not require map keys to equal block starts, blocks to be nonempty and pairwise disjoint, or the freelist to correspond to outstanding allocations. Likewise, the success postconditions for `alloc_specific` and `alloc` expose size/bounds but no exclusive allocation effect, so a verified client cannot obtain the allocator behavior described by “Allocates”/“Frees,” while the verifier accepts executions that violate it.
- **Suggested correction:** Model allocator state explicitly. At minimum, strengthen the locked invariant with key/start consistency and ordered pairwise-disjoint free blocks, and give successful `alloc`/`alloc_specific` calls an allocation capability tied to this allocator identity and the returned/requested range. Require `free` to consume that capability (not a persistent initialization witness), and specify the corresponding state transition: success removes that range from the free set and `free` adds it back while preserving disjointness. If allocation tokens are deliberately out of scope, the contracts still need an abstract allocated/free-set model with a precondition excluding double-free and arbitrary free, plus postconditions that expose the allocation effects to callers.

## Medium

None.

## Low

None.

## Evidence check record

- Read all 543 lines of `diff.patch`; checked the complete changed `range_alloc.rs` in `after/` and the corresponding file in `before/` for context.
- Traced token creation and duplication through `FreelistResource`, `FreelistInvariant::inv`, `get_freelist_guard`, both allocation methods, and `free`. Static refutation failed: no clause relates the persistent witness to a range or requires freelist entries to be disjoint.
- Inspected the live `IoMemAllocator` caller context. Its unsafe `recycle` documentation requires ownership, but that condition is not represented in `RangeAllocator::free`'s changed Verus contract and therefore cannot establish or preserve the missing allocator property for verified callers.
- The patch contains no `#[verifier::rlimit(...)]` change and no new or materially changed external specification for a `std`, `core`, or `alloc` API.
- No verification was performed: Verus, tests, CI, experiments, and repository history were intentionally not run under the fast-review override. Findings are based on static contract and implementation evidence only.
