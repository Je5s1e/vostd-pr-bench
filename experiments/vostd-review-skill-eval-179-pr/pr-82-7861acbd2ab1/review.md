# Review: PR #82 snapshot `7861acbd2ab1` (`diff.patch`)

> Scope: static review of `diff.patch` against the supplied `before/` and `after/` snapshots. The patch changes `vstd_extra/src/extra_num.rs`, including the `impl_external_ilog2!` macro and a new generated `ilog2` lemma.

**Bottom line:** The modified macro still gives the panicking integer `ilog2` operation a trusted specification with no nonzero precondition. That permits verified callers to invoke the executable operation on zero even though Rust specifies that case to panic, so the trust boundary is incomplete and this snapshot should not merge as-is. No other strong, evidence-backed issues were found in the supplied patch.

## High

### The trusted `ilog2` specification omits its required nonzero precondition

- **Guideline:** `complete-external-contracts`
- **Location:** `vstd_extra/src/extra_num.rs:422` (scope evidence: the modified macro parameters at line 414 and the newly generated lemma at line 478)
- **Evidence:** The macro installs an external specification for every unsigned integer type:

  ```rust
  #[verifier::external_fn_specification]
  #[verifier::when_used_as_spec($spec_name)]
  pub fn $ext_fn_name(x: $uN) -> (res: u32)
      ensures
          res == log(2, x as int),
  {
      x.ilog2()
  }
  ```

  It has no `requires` clause, while Rust's unsigned-integer `ilog2` operation panics when `x == 0`. The same generated API also exposes contracts mentioning `x.ilog2()` for unconstrained inputs, for example `pub proof fn $log2_bounds_lemma(x: $uN)` at lines 449–452 and `$ilog2_ordered_lemma` with only `x <= y` at lines 467–471.
- **Problem:** This trusted boundary models a partial, panicking executable operation as callable for every unsigned value. A verified caller can therefore call `ilog2(0)` without proving the operation's real non-panicking condition; the mathematical postcondition does not repair that missing executable precondition.
- **Suggestion:** Specify the primitive directly with an `assume_specification[$uN::ilog2]` that requires `x > 0`, returns `log(2, x as int) as u32`, and records the appropriate `no_unwind`/invariant policy. Propagate or prove `x > 0` anywhere the modeled operation is used. The new power-of-two lemma can discharge this from `is_power_2(x as int)`; the unconstrained bounds and ordering lemmas need explicit positive-input preconditions (and ordering needs both operands positive).

## Medium

No findings.

## Low

No findings.

## Evidence check record

- Read all 171 lines of `diff.patch` and the complete supplied before/after versions of `vstd_extra/src/extra_num.rs` (699 and 742 lines respectively).
- Checked the changed contracts, generated public proof APIs, recursive power-of-two proof, macro expansion inputs, assumptions, invariants, and trust boundary. No `#[verifier::rlimit(...)]` change exists, so the `> 200` workflow check was not triggered.
- The patch does not add or materially change a `std`/`core`/`alloc` external specification contract; the concern above is that the materially modified macro retains an already incomplete trusted boundary. No separate `upstream-reusable-specs` finding was recorded.
- Static refutation check: Rust's unsigned `ilog2` contract excludes zero. As corroborating history, the next PR commit (`9797a63e697a4f901a0a2e14c586729beed79a00`, outside this reviewed snapshot) replaced this wrapper with a direct `assume_specification` carrying `requires x != 0` and `no_unwind`; the following commit normalized it to `x > 0`. This confirms that the missing condition is not an intentional total model.
- The `<` to `<=` change in the `pow2` lemma was not reported: for the unsigned types instantiated here, `MAX = 2^BITS - 1`, so no power of two equals `MAX`; the change does not itself create a false contract.
- No repository history, Verus execution, CI run, caller experiment, or exhaustive guideline checklist was performed, per the requested fast-review override. Conclusions are limited to static evidence in the supplied snapshots plus the narrowly cited public API/history evidence above.
