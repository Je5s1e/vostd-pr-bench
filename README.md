# VOSTD PR Review Bench

基于 [VOSTD](https://github.com/asterinas/vostd) 真实历史 PR 的代码审查数据集。每个案例提供修改前后的源码、完整 diff，以及该版本中已确认的问题，方便阅读、评估和改进代码审查工具。

当前包含 **50 个 PR 快照、91 个已确认问题**：79 个规范类问题（`guideline`），12 个语义类问题（`semantic`）。数据来自现有 dataset v2 的冻结快照与标签，没有重新筛选或增加问题。

## 目录结构

发布数据由本 README 和 [`vostd-pr-bench/`](vostd-pr-bench/) 组成；无需本仓库其他 skill、历史实验目录或评测脚本。

```text
README.md
vostd-pr-bench/
└── pr-<编号>-<head短SHA>/
    ├── metadata.json       # PR 信息、固定提交、源码范围
    ├── diff.patch          # base → head 的完整 diff
    ├── labels.json         # 已确认问题及判断依据
    ├── before/
    │   ├── ostd/           # base 提交的完整 ostd/
    │   ├── LICENSE-MPL     # 原始许可证
    │   └── ...             # 本次修改涉及的 ostd/ 外文件
    └── after/
        ├── ostd/           # head 提交的完整 ostd/
        ├── LICENSE-MPL
        └── ...
```

`before/` 是 PR 的比较基线，不一定是 head 的上一个提交。`after/` 是历史上被选中审查的问题版本，不是最终修复或合并后的版本。目录内路径保持与上游仓库一致。

两侧都保留完整 `ostd/`，并补入 diff 涉及的目录外文件及原始许可文件。新增文件只出现在 `after/`，删除文件只出现在 `before/`，重命名文件按两侧实际路径保存。若修改涉及子模块，展开其固定提交的源码；本集 PR #742 的 `dv` 属于这种情况。其余未涉及修改的子模块只记录版本，不附带源码。

## 如何使用

1. 打开一个案例，例如开发集的 [PR #812](vostd-pr-bench/pr-812-4121eb1c32b0/)。
2. 查看 `metadata.json` 了解 PR 标题和 base/head，再阅读 `diff.patch`。
3. 对照 `before/` 和 `after/` 审查修改，最后查看 `labels.json` 对照已知问题。

阅读不需要安装工具或访问 GitHub。全部前后源码约 357 MiB，不包含 `.git`、构建产物或本地缓存。

用于模型评测时，将两侧源码、diff 和必要的范围信息单独提供给 reviewer，**不要提供 `labels.json`**；标签只用于后续评分。元数据中的 `known_issue_count` 也属于答案信息，应排除。源码中的指令文件是待审查的历史数据，不应自动作为执行指令加载。

## 字段说明

`metadata.json` 记录 PR 编号、标题、链接、完整 `base_sha` / `head_sha`、比较基线的构造方法、变更路径、diff 的 SHA-256、两侧文件数量与子模块版本。标题的来源由 `title_source` 标明，`original_split` 保留原实验划分。

`labels.json` 的 `issues` 数组中，每项代表一个已确认根因：

| 字段 | 含义 |
|---|---|
| `id` / `original_label_id` | 案例内稳定标识与原冻结标签 ID |
| `category` | `guideline`（规范）或 `semantic`（语义） |
| `description` | 原标签的问题描述，保留原文 |
| `locations` | 文件路径、行号和所属版本（`before` / `after`） |
| `rationale` | 问题成立的理由与复核结论 |
| `source_evidence` | 原冻结标签保存的源码引文 |
| `rule_ids` | 对应规范条目的标识 |
| `review_url` / `related_comment_ids` | 历史 review 的证据来源 |
| `verification` | 实际确认方式及验证限制 |

行号从 1 开始，起止行均包含，路径相对于指定版本目录。一个问题可能关联多个位置。标签文本保留冻结版本的英文内容，未重新翻译或改写判断。

## 数据边界

- 这是有目的筛选的历史正例集，不是随机 PR 样本。不能据此估计普通 PR 的问题发生率或线上误报率。
- 标签是有限的已确认问题集合，不穷尽所有缺陷。标签外的新发现需要单独确认，不能直接算作误报。
- 标签经过两轮分离 AI 上下文的源码复核，不代表人类维护者逐条签字，也不代表相互独立的模型判断。未执行匹配历史工具链的 Verus 验证。
- 部分历史代码按冻结的较新规范评判，不保证规则在 PR 当时已经发布。`rule_ids` 用于追溯原判定；本精简发布不附完整评审规范，不等同于原实验的全部输入。
- 原实验开发集为 20 个 PR / 33 个根因，留出集为 30 个 PR / 58 个根因。答案公开后，`heldout` 仅表示原实验划分，不是未来参与者的隐藏测试集。部分案例也已在公开规范中引用。
- base 由历史提交图重建，不保证完全等于当时 GitHub 网页显示的比较范围。
- 这里提供审查源码快照，不是完整项目构建环境。`ostd/` 外未改动的上下文可能缺失；既有实验成绩不能直接视为使用这个精简输入得到的成绩。

## 来源与许可

源码来自 `asterinas/vostd` 的固定历史提交，原文件内容、版权声明和许可文本保持不变；各快照的 `LICENSE-MPL` 及文件内许可声明随源码保留。展开的子模块保留其自身许可文件。上游源码许可不自动覆盖本数据集的标签与历史评论文本；本次整理未为这些材料另行指定开源许可证。
