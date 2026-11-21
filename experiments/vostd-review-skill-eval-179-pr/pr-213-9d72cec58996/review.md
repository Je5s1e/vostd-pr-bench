# Review: PR 213 snapshot 9d72cec58996

> Fast, non-exhaustive review using `diff.patch` as the authoritative change and `before/` / `after/` only for context and source line numbers.
> Scope: the 14-file patch adding the sync models and the `vstd_extra` state-machine and temporal-logic support.

**Bottom line:** The abstract-lock proof admits a preservation obligation that is false for a reachable state, and the advertised mutual-exclusion result depends on that unproved invariant; this blocks merging the proof as verified. The patch also introduces two avoidable sources of model drift: an `actions` field that does not constrain `StateMachine::next_result`, and duplicate hand-written and macro-generated mutex models.

## High

### The admitted `cs` case hides a false invariant used to prove mutual exclusion

- **Guideline:** `centralize-trusted-boundaries`
- **Location:** `specs/ostd/src/sync/abstract_lock.rs:340`
- **Evidence:** `cs().forward(tid)(s, s_prime) ... implies s_prime.not_locked_iff_no_cs()` is closed with `admit();` at lines 340–344. The claimed invariant is `(!self.locked <==> ...pc[tid] == Label::cs...is_empty()) && (self.locked <==> ...is_singleton())` at lines 209–212. But `cs()` changes the owner's PC from `Label::cs` to `Label::unlock` without clearing `locked` (lines 125–147), so the reachable trace `init -> start -> acquire_lock -> cs` ends with `locked == true` and no process at `Label::cs`, directly falsifying both equivalences. `lemma_mutual_exclusion` then calls this admitted lemma at line 361 and derives its result from it at lines 365–376.
- **Problem:** This is not merely unfinished proof debt: the admitted preservation statement is false under the newly defined transition system. Consequently the patch's mutual-exclusion theorem is not established by checked reasoning.
- **Suggestion:** Replace `not_locked_iff_no_cs` with an inductive invariant that reflects the interval during which the lock remains held (for example, distinguish the owner/release phase, or prove the weaker facts `!locked ==> no process is in cs` and `at most one process is in cs`). Prove every transition case without `admit()`, then make `lemma_mutual_exclusion` depend only on that checked invariant.

## Medium

### `StateMachine::actions` does not constrain the action selected by `next_result`

- **Guideline:** `implement-inv-for-models`
- **Location:** `vstd_extra/src/state_machine/state_machine.rs:23`
- **Evidence:** The public field is documented as `// The set of actions the state machine can take.` and declared as `pub actions: Set<Action<...>>` at lines 26–27. However, `next_result` chooses any `step` whose mapped action is enabled (lines 44–55) and executes `(self.step_to_action)(witness_step)` (lines 55–60), with no requirement that this action belongs to `self.actions`. No `Inv` implementation relates `step_to_action` to `actions`.
- **Problem:** A legal `StateMachine` value can return a transition from an action explicitly absent from its advertised action set, so the model's stated abstraction is not enforced and callers cannot rely on the field's meaning.
- **Suggestion:** Either remove `actions` if `step_to_action` is the sole source of allowed actions, or add an intrinsic `Inv` requiring every mapped action to belong to `actions` and require that invariant at operations that use the mapping. If membership is intended to be checked per transition, include it consistently in both the existential and the `choose` predicate.

### The mutex transition system is maintained twice

- **Guideline:** `reuse-existing-specifications`
- **Location:** `specs/ostd/src/sync/mutex_verussync.rs:35`
- **Evidence:** `mutex.rs` defines `Label`, `Procedure`, `StackFrame`, `ProgramState`, every transition, and `mutual_exclusion`; `mutex_verussync.rs` independently repeats the same enums and frame and restates the transition system with `state_machine!`. For example, the hand-written `pre_check_lock` at `mutex.rs:62–84` and macro transition at `mutex_verussync.rs:62–74` perform the same lock test and updates, while both modules separately define `mutual_exclusion` (`mutex.rs:349–354`, `mutex_verussync.rs:213–218`). Both are publicly exported from `sync/mod.rs:3–4`.
- **Problem:** There are now two public, independently editable specifications of the same mutex protocol with no correspondence theorem or stated distinction. Any later protocol fix can silently update one model but not the other.
- **Suggestion:** Choose one representation as the canonical model and build proofs on it. If the duplication is intentionally a comparison or migration, keep one adapter/translation layer and prove correspondence, rather than duplicating all states and transitions.

## Low

No low-severity findings retained.

## Evidence check record

- Read the complete authoritative `diff.patch` scope structurally and inspected the added proof/model sources in `after/`, using `before/` to confirm that the affected modules are newly introduced.
- Searched the patch and added Verus sources for `admit`, `assume`, external/trusted declarations, and `#[verifier::rlimit(...)]`. Three active `admit()` calls were found in `abstract_lock.rs`; no changed rlimit and no new `std`/`core`/`alloc` external specification was found.
- Refuted the admitted `cs` preservation premise statically from the definitions: `acquire_lock` sets `locked = true` and returns to `Label::cs`; `cs` advances the PC to `Label::unlock` while preserving `locked = true`, contradicting `not_locked_iff_no_cs`.
- Compared the two newly exported mutex modules transition-by-transition at representative definitions and confirmed that they independently encode the same protocol.
- **No-verification disclosure:** Per the requested fast-review override, no Verus invocation, build, test, isolated caller experiment, history analysis, or exhaustive guideline checklist was performed. Findings are based on the immutable patch and supplied before/after source context only.
