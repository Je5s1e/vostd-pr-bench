# VOSTD PR Review Bench

A code review dataset built from historical pull requests in [VOSTD](https://github.com/asterinas/vostd). Each case includes source code before and after the changes, the complete diff, and confirmed issue labels for evaluating and improving code review tools.

## Dataset Statistics

| Metric | Count |
|---|---:|
| Unique PRs | 164 |
| Reviewed head commits | 179 |
| Issue labels | 244 |

## Historical Review Statistics

A review of **238 PRs** updated between **2026-08-15 and 2026-11-12** collected 877 inline comments, 290 discussion comments, and 663 submitted reviews. After excluding self-reviews, explanations, and repeated feedback, 492 inline feedback items were classified; 56 PRs contained classified feedback across all review sources. These historical feedback counts are separate from the confirmed labels above.

## Issue Categories

| Category | Issue labels | Examples |
|---|---:|---|
| Semantic (`semantic`) | 133 | Runtime behavior changes, incomplete contracts, incorrect models or invariants |
| Guideline (`guideline`) | 111 | Proof organization, naming, redundant helpers, failure to reuse existing specifications |

## Data Structure

```text
vostd-pr-bench/
└── pr-<number>-<short-head-SHA>/
    ├── metadata.json   # PR title, URL, base/head commits, and changed paths
    ├── diff.patch      # Complete diff from base to head
    ├── labels.json     # Issue categories, descriptions, locations, and rationale
    ├── before/         # Source code before the changes
    └── after/          # Source code under review
```

Source trees preserve upstream paths and include `ostd/` where present, changed files, and additional context. `before/` and `after/` correspond to the base and head commits. The code in `after/` still contains the labeled issues.

## Usage

**Evaluating a code review tool or model** (see [PR #812](vostd-pr-bench/pr-812-4121eb1c32b0/) for an example):

1. Provide `diff.patch` and the source context in `before/` and `after/`. Use the PR title, commits, and changed paths from `metadata.json` if needed.
2. Ask the tool to identify guideline or semantic issues and report each issue's file path, line numbers, description, and rationale.
3. Save the results, then compare them with `labels.json`. Confirmed labels may not cover every issue; verify additional findings separately.

Keep `labels.json`, `known_issue_count`, and historical review records out of the tool's input and reserve them for scoring.

**Exploring cases**: Read `labels.json`, follow its `locations` into the source, and use the descriptions, rationale, and diff to understand each issue. All files can be read locally without installing tools or accessing GitHub.

Source code retains upstream copyright notices and license files. See the licenses and file notices included with each case.
