# Review: PR #871 (`diff.patch`, head snapshot `61c301b7f35d`)

> Fast isolated review of the authoritative patch plus the supplied `before/` and `after/` context. The patch contains CI, Python, JavaScript, HTML, and CSS changes only; it changes no Verus proof/API contract, trusted external specification, or `#[verifier::rlimit]` setting.

**Bottom line:** The new dashboard can publish materially false verification-coverage data because per-file `line_count` failures are converted into zero-valued reports while the snapshot command still succeeds. The workflow is also not idempotent for an unchanged rerun, and its advertised parallelism is never used, making the new 30-minute job unnecessarily vulnerable to timeout. The first issue should block publication until failures abort snapshot generation.

## High

### Failed `line_count` runs are published as valid zero coverage

- **Category:** Assumption / publication invariant
- **Location:** `tools/verus_stats.py:247-269`, `tools/verus_stats.py:285-307`, `tools/verus_stats.py:437-461`
- **Evidence:** `run_line_count_file` returns `(None, error)` on a nonzero exit or invalid JSON. `collect_coverage` nevertheless stores that `None` in `vostd_reports` or `mainline_reports`, and `classify_lines(None)` returns all-zero buckets. The error is only appended to `warnings`; `cmd_snapshot` writes the snapshot and returns `0` after `print_report(modules, warnings)`.
- **Problem:** A failed VOSTD count is presented as unverified whenever its mainline twin succeeds; a failed mainline count can clamp a successfully counted VOSTD file to a zero budget and remove it from the emitted module list. A partial tool failure therefore produces a green CI job and a misleading verification dashboard instead of withholding invalid data.
- **Suggestion:** Treat every per-file `line_count` error as fatal before `write_snapshot`, reporting all affected paths and exiting nonzero. If partial results are intentionally supported, represent failed files explicitly and prevent totals/snapshots from being published as coverage until the dataset is complete.

## Medium

### An unchanged workflow rerun fails at `git commit`

- **Category:** Maintainability / idempotent publication contract
- **Location:** `.github/workflows/ci.yml:391-414`, `tools/verus_stats.py:480-488`
- **Evidence:** `cmd_record` explicitly updates an existing point for the same SHA (`existing.update(point)  # reruns refresh the same commit`), after which the workflow copies the snapshot and unconditionally runs `git ... commit`. With the same snapshot and history bytes, Git exits nonzero with nothing to commit, and `set -e` terminates the job before the push/deployment path.
- **Problem:** Re-running a successful workflow for the same commit is a normal supported operation, but an unchanged rerun makes `perf-history` fail and consequently prevents `doc-deploy` from satisfying its success dependency.
- **Suggestion:** Test whether `git diff --cached --quiet` after `git add stats`; commit and push only when data changed, otherwise report that the SHA is already recorded and continue successfully.

### `--jobs` does not parallelize any counting work

- **Category:** Maintainability / resource-bound assumption
- **Location:** `tools/verus_stats.py:251-269`
- **Evidence:** A `ThreadPoolExecutor(max_workers=jobs)` is created as `pool`, but `pool.submit`, `pool.map`, and the `pool` variable are never used. Both list comprehensions invoke `run_line_count_file(...)` directly and sequentially before their result loops begin.
- **Problem:** The CLI and implementation imply bounded parallel counting, but every VOSTD and mainline Rust file starts a separate `line_count` process serially. This can needlessly exhaust the new job's 30-minute timeout as the source tree grows.
- **Suggestion:** Submit each keyed file to the executor (or use `pool.map`) and collect futures deterministically; alternatively remove `--jobs` and size the CI timeout for an explicitly sequential implementation.

## Low

No evidence-backed low-severity findings.

## Evidence check record

- Read all 1,518 lines of `diff.patch` and inspected the cited files in the supplied `after/` tree with line-numbered context; consulted the corresponding `before/` tree for scope (all three cited implementations are newly introduced).
- Searched the authoritative patch for Verus proof/API changes, trusted/external specifications, and `#[verifier::rlimit]` changes. None are present, so proof reuse, trusted-model soundness, API pre/postcondition, upstream-spec, and rlimit-cap checks are not applicable.
- Refutation check for the High finding: confirmed `classify_lines(None)` produces zeros, failed reports remain present in the report dictionaries, warnings do not alter the exit status, and snapshot emission precedes the successful return.
- Refutation check for rerun idempotence: confirmed same-SHA history entries are updated in place, while the workflow has no staged-diff guard around the unconditional commit.
- Refutation check for parallelism: confirmed the executor object has no consumer and both subprocess calls occur inside ordinary eager list comprehensions.
- Per the requested fast-review override, no history inspection, Verus invocation, tests, browser checks, or isolated experiments were performed. Conclusions are static-review findings only; CI/verification was not rerun.
