# PR #933 定向 A/B 实验协议

## 目的与版本

评估 PR #933 的 review persona 补充能否帮助发现相关历史问题，并提高建议的正确性。原版固定为 PR merge-base `032089aa3d4603fa68f3f874cddfc6d61ff81225`；优化版固定为 `cc0b47efab48260764a6d4f989bdcb1cfbf30155`。完整 skill 保存在 skills/，原始差异保存在 skill.diff。两版共享 merge-base 的 coding-guidelines；两版改动只有两个 persona 文件。

Reviewer 原话：Explain why these changes are needed?
来源：https://github.com/asterinas/vostd/pull/933#issuecomment-6911880046
读取日期：2026-11-16。没有向 GitHub 发送评论。

## 预先选定样本与目标

| PR | 对应改动 | 目标问题与命中条件 |
|---|---|---|
| 628 | name-proof-roles | 指出 list_store 中资源转移 proof helper 缺少 tracked_ 前缀；只建议 lemma_ 不算正确修复。另记录 unit-returning push helper 是否覆盖，不把它另算 bench 标签。 |
| 632 | 资源记账模型检查 | 明确指出 public ghost ledger 可被清空而保留 tracked token，clean_inv 因而不能证明已无未偿还 obligation。仅泛称 ghost 不安全不算完整命中；不能把它夸大成已证明运行时内存错误或 SMT 矛盾。 |
| 770 | defer-auxiliary-proof-functions | 指出 lemma_cpucount_fits 等私有辅助证明插在 API 中间，应放到末尾；不要求移动所有 public/critical proofs。 |
| 856 | group-imports-by-crate | 指出同组的 vstd arithmetic/prelude 导入拆分；修复应保留 cfg(irc11) 条件，避免跨 inherited exec/verification 分组盲目合并。 |
| 886 | match-enum-results | 找到 None 等价式中 no-match ⇒ None 的冗余方向，保留 None ⇒ no-match 和 Some payload/first-match 事实；删除整个 None 子句不算正确修复。 |
| 931 | preserve-exec-code | 指出原始 mem_size 注释被替换，要求在 proof work 中保留原文；不要误称邻近未变的 resize/copy 行为被这次改动修改。 |

另计 #770 quantifiers-and-triggers 标签作为非直接目标对照，共 7 个范围内 bench 标签、6 个定向目标。标签在选择阶段由主代理读取；审查代理不接收标签或上述选样理由。

## 执行与隔离

- 使用 skill 的 files 模式：每个 PR 只审查一个完整目标文件；其他源码及 before/diff 仅作上下文。因此不是完整 PR diff 模式评测，不统计目标文件之外的问题。
- 每版分别运行 maintainability、proof-engineering、specification 三个独立无历史代理，按相同案例顺序审查；每个 persona 一次批次，分别保存每例 Findings/Compliance。共六次 persona pass、36 份案例输出；每版每例一次，无失败结果挑选或重试取优。
- 代理使用本会话默认配置，不人为更改模型或推理设置；具体底层模型标识、seed、采样温度未由 spawn 接口暴露，不能声称这些值经过显式锁定。
- 两版共享不可变源码副本与规范。输入目录不包含 labels.json、known_issue_count、original_split。代理不得读取其他版本、其他 persona 输出、bench 标签和历史 review，且不得联网。
- 保留未经改写的完整规范，其中自身包含历史 PR 示例和链接；这是两版相同的先验信息，因此并非没有任何历史案例信息的完全盲测。禁止访问链接。试验只隔离额外标签与 reviewer 记录。
- 测试源来自指定历史提交，采用现行冻结规范。这是对现行 skill 的回归测试，不重建历史时点的审查政策。
- files 快照与自身锚点无新增修改，未激活 workflow persona；该 persona 在 PR #933 中也未修改。
- 与通常 skill 流程的适配：bench 文件快照替代 checkout/提交序列；冻结规范替代运行中更新规范；不联网检索上游模型，缺失历史 vstd/工具链明确记录。主代理按已授权实验需求持久保存结果；不修改原始 bench 或现有 vostd 工作树。
- 目标及上下文哈希见 input-hashes.json；完整上下文可从 bench 相同目录重建，精确目标文件和 diff 另存 inputs/。运行临时目录及提交见 manifest.json。提示词见 prompts/。

## 评分方法

先冻结独立原始输出，再由主代理对照 gold.json 和源码判定。以根因为单位，不按措辞完全匹配；同一问题跨 persona 去重。分类为完整命中、部分命中、漏检；另记录修复建议是否保留语义、是否存在无证据夸大。

人工核对所有额外发现，区分 confirmed、uncertain、refuted；未匹配已知标签不自动算误报。汇总报告应区分新增发现率和证据/建议质量。未经全面补充标注，不给整个 bench 的 precision 或 F1。

## 结论边界

样本按本 PR 的改动挑选，具有选择偏倚；现行规范也吸收了历史 review。单次、小样本、没有独立留出集，不能证明总体提升或稳定因果效应。观察不到改进时如实报告，不能用补充提示或标签指导重跑制造提升。尚未覆盖的子改动（alias/shadowing、历史标记恢复、求值顺序/panic、所有权 API 误命名等）不能宣称已经验证。
