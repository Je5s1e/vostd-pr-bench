# Review: PR #220 problem snapshot `cfcd9e87ed0d`

> Fast, non-exhaustive VOSTD review of `diff.patch`, with the captured `before/` and `after/` files used only for context. The reviewed patch changes `.github/workflows/verus-update-test.yml`; it contains no Verus API, proof, external specification, or `#[verifier::rlimit]` change.

**Bottom line:** The two added `fi` statements repair the workflow's unterminated shell conditionals, but the same patch makes both phase-II bootstrap commands unconditionally non-fatal. Because this job gates a success dispatch used for promotion, a failed toolchain bootstrap can now fall through to later steps and potentially produce a successful gate without establishing that the intended Verus toolchain was built. This is a trust-boundary regression and should block this snapshot from merging.

## High

### Bootstrap failures are suppressed in a promotion gate

- **Location:** `.github/workflows/verus-update-test.yml:49-50`
- **Area:** proof/trust boundary; verification-gate fail-closed behavior
- **Evidence:** The patch changes both required setup commands from `cargo dv bootstrap --restart` and `cargo dv bootstrap --upgrade --test_branch` to `cargo dv bootstrap --restart || true` and `cargo dv bootstrap --upgrade --test_branch || true`. The resulting workflow later declares success based only on the `make` log's literal `error:` text (`:51-60`) and dispatches `verus-update-test-success` under `if: success()` (`:66-73`).
- **Problem:** `|| true` converts every bootstrap failure—regardless of cause—into success. The remaining checks do not prove that bootstrap completed or that `make` used the requested phase-II toolchain, so this gate can continue toward a promotion signal after its verification environment failed to initialize.
- **Suggestion:** Remove both `|| true` suffixes so bootstrap remains fail-closed. If a particular bootstrap exit is known to be benign, handle only that documented condition explicitly and separately verify that the expected toolchain/artifacts exist before running `make` and allowing the success dispatch.

## Medium

No findings.

## Low

No findings.

## Evidence check record

- Read all 47 lines of `diff.patch` and compared the affected region against the captured `before/.github/workflows/verus-update-test.yml` and `after/.github/workflows/verus-update-test.yml`.
- Confirmed the suppression is introduced by this snapshot: the before file has the two bootstrap commands without `|| true`; the after file has the suppressions at lines 49-50.
- Confirmed the impact path statically: after the suppressed commands, the job runs `make`, searches its log only for `error:`, prints a verification-passed message otherwise, and conditionally sends the success dispatch when the job is successful.
- The added `fi` statements at after-file lines 41 and 60 correctly close the two visible `if` statements. The whitespace-only edits do not create a review issue.
- No changed `#[verifier::rlimit(...)]` exceeds 200, and no reusable `std`/`core`/`alloc` external specification is added or materially changed; those narrowly scoped workflow checks are not triggered.
- No executable/proof API contract, invariant, assumption, or spec-reuse opportunity is changed in the reviewed patch.
- **No-verification disclosure:** Per the requested fast-review override, no Verus run, CI execution, shell experiment, repository history analysis, or exhaustive guideline checklist was performed. The finding is based on static control-flow evidence in the supplied patch and captured before/after files.
