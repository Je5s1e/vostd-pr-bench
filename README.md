# VOSTD PR Review Bench

基于 [VOSTD](https://github.com/asterinas/vostd) 历史 PR 的代码审查数据集。每个案例包含修改前后的源码、完整 diff 和已确认的问题标签，可用于代码审查工具的评估与改进。

## 数据统计

| 指标 | 数量 |
|---|---:|
| PR 快照 | 50 |
| 已确认问题 | 91 |
| 规范类问题（`guideline`） | 79 |
| 语义类问题（`semantic`） | 12 |
| 原开发集（`dev`） | 20 个 PR / 33 个问题 |
| 原留出集（`heldout`） | 30 个 PR / 58 个问题 |

## 数据结构

```text
vostd-pr-bench/
└── pr-<编号>-<head短SHA>/
    ├── metadata.json   # PR 标题、链接、base/head 提交及变更路径
    ├── diff.patch      # base → head 的完整 diff
    ├── labels.json     # 问题类别、描述、代码位置及判断依据
    ├── before/         # 修改前的源码
    └── after/          # 待审查版本的源码
```

两侧源码包含完整 `ostd/` 及本次修改涉及的目录外文件，路径与上游仓库一致。`after/` 对应选定的历史审查版本。

## 使用方法

1. 选择一个案例，例如 [PR #812](vostd-pr-bench/pr-812-4121eb1c32b0/)。
2. 阅读 `metadata.json` 和 `diff.patch`，结合 `before/`、`after/` 中的源码审查修改。
3. 将审查结果与 `labels.json` 中的已知问题对照；标签包含问题描述、位置和判断依据。

数据可直接在本地阅读，无需安装工具或访问 GitHub。用于模型评测时，提供源码和 diff，将 `labels.json` 及元数据中的 `known_issue_count` 留作评分信息，不作为模型输入。

源码保留上游版权声明与许可文件，详见各快照中的 `LICENSE-MPL` 及文件内声明。
