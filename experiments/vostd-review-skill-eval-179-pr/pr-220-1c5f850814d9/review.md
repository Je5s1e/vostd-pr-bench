# Review: PR #220 (`1c5f850814d95ccfdddf217d9def5f5a67e595e1..503ca46c41ce3d491323bc992721da0ffcb66ef1`)

> Scope: the authoritative `diff.patch`, which adds `.github/workflows/verus-update-test.yml`; supplied before/after context was consulted. Fast isolated review: maintainability, verification/trust assumptions, contracts/invariants, `rlimit > 200`, and reusable external specifications.

**Bottom line:** The workflow can report successful verification after `make` has failed, so it is not a sound promotion gate. It also switches superproject branches without realigning recursive submodules, making the revisions under test dependent on the dispatch-supplied checkout. Fix both issues before relying on the success dispatch.

## High

### The verification gate discards `make`'s exit status

- **Location:** `.github/workflows/verus-update-test.yml:37-45`, `.github/workflows/verus-update-test.yml:55-63`
- **Area:** proof/trust assumption (sound verification gate)
- **Evidence:** Both test commands are pipelines: `VOSTD_VERIFY_PARALLEL=1 make 2>&1 | tee verus_main.log` and `make 2>&1 | tee verus_phaseII.log`. The only subsequent failure test is the exact textual search `if grep -q "error:" ...`; otherwise the workflow prints `Verification passed!`.
- **Problem:** No `pipefail` or explicit `${PIPESTATUS[0]}` check is present. Under the default implicit Linux shell, the pipeline status is `tee`'s status, so a nonzero `make` result is lost. A failure that does not emit the exact lowercase substring `error:` (for example, a `make: *** ... Error 2` failure) reaches the success branch and can trigger promotion despite failed verification.
- **Suggestion:** Preserve and require the `make` status independently of log parsing. For example, run the step with Bash, capture `make_status=${PIPESTATUS[0]}` immediately after the pipeline, emit any desired annotations from the log, and `exit "$make_status"` when it is nonzero. Apply the same structure to both test blocks.

## Medium

### Branch switches leave the dispatch-selected submodule revisions in place

- **Location:** `.github/workflows/verus-update-test.yml:19-23`, `.github/workflows/verus-update-test.yml:33-36`, `.github/workflows/verus-update-test.yml:50-54`
- **Area:** reproducibility/invariant assumption
- **Evidence:** The initial checkout selects `${{ github.event.client_payload.branch }}` with `submodules: recursive`. The later transitions use only `git checkout main` and `git checkout phaseII/verified`; neither transition runs `git submodule update` or performs a fresh recursive checkout.
- **Problem:** Checking out another superproject revision changes recorded gitlinks but does not, by default, update the already checked-out submodule worktrees. The workflow therefore does not establish the invariant that each branch is tested against its own recursive submodule revisions; the main and phaseII runs can inherit revisions selected by the dispatch payload or the preceding run.
- **Suggestion:** Use a clean `actions/checkout` step with `submodules: recursive` for each tested ref, or after every branch switch run `git submodule sync --recursive` and `git submodule update --init --recursive --force`. Prefer separate clean worktrees/jobs if generated state must also be isolated between the two runs.

## Low

No low-severity findings.

## Evidence check record

- Read the complete authoritative patch and all supplied before/after files. The before/after bundle contains only unchanged license files, so it supplies no additional workflow context.
- Treated `diff.patch` as authoritative as requested. The auxiliary metadata calls the path modified with 4 additions and 1 deletion, while the authoritative patch represents a 70-line new file; the metadata was therefore not used to narrow the review.
- Statically checked both verification blocks: each has the same `make | tee` status-loss pattern and exact `grep -q "error:"` fallback.
- Checked branch-transition semantics against the commands in the patch: no recursive submodule synchronization/update occurs after either `git checkout`.
- No `#[verifier::rlimit(...)]` change exists, so the `rlimit > 200` check is not triggered. No Verus/Rust API, contract, invariant definition, or `std`/`core`/`alloc` external specification is added or changed, so API-contract and spec-reuse checks found nothing in scope.
- **No-verification disclosure:** Per the fast-review override, no history analysis, Verus run, exhaustive rule pass, caller experiment, CI execution, or other dynamic experiment was performed. Findings are based on the static workflow semantics visible in the authoritative patch.
