# PR #933：原版与优化版 vostd-code-review 对照结果

## 结论

**本轮观察到局部收益，最有力的证据是 #632 的资源记账漏洞；不能据此宣称所有优化都有效。**

在预先按 PR 改动挑选的 6 个目标问题上，原版命中 **4/6**，优化版命中 **5/6**。新增命中来自修改后的 proof-engineering persona。其余四个命中两版共有；#886 的枚举契约冗余两版都漏检。优化版对 #628 的无返回值所有权 helper 明确列举更充分，但这仍是同一个已知标签，不计为新增命中。

这是单次、定向、小样本回归观察，不是独立留出集评测。没有多次重复，也没有显式固定 seed/temperature，因此结果支持“这条检查在本轮帮助发现了问题”，不支持稳定因果提升或全 bench 提升的结论。

## 固定版本与实验方式

- 原版：`032089aa3d4603fa68f3f874cddfc6d61ff81225`，PR #933 的 merge-base。
- 优化版：`cc0b47efab48260764a6d4f989bdcb1cfbf30155`，读取时的 PR head。
- 已通过 Git fetch 获取上游 main 和 PR head，再按 SHA 导出完整 skill；未切换或修改现有 vostd 工作树。
- 共享规范：固定原版提交的完整 coding-guidelines。skill 核心和 specification persona 完全相同，只有 maintainability、proof-engineering persona 不同。
- 每例审查一个完整目标文件，使用 skill 的 files 模式。两版获得相同的 before/after 上下文和 diff；不是整份 PR 的 diff 模式审查。
- 两版各执行 maintainability、proof-engineering、specification 三个无历史独立代理，共 **6 次 persona pass、36 份案例原始输出、12 份综合审查报告**。
- 代理不接收标签或预期问题，不读取另一版输出，不访问历史 review。原始规范本身包含历史案例示例，两版共享这些先验，因此不是完全无历史知识的盲测。
- 未运行历史 Verus、CI 或修复验证。工具链和部分依赖缺失被明确记录；全部结论属于源码与契约层面的审查。

完整预设条件见 [protocol.md](protocol.md)，改动与选样关系见 [change-map.md](change-map.md)。

## 逐项比较

| 对应优化 | Bench PR | 原版 | 优化版 | 本轮解释 |
|---|---|---|---|---|
| 所有权 helper 命名 | [#628](https://github.com/asterinas/vostd/pull/628) | 命中 | 命中 | 两版都建议 tracked_；新版明确列出返回 unit 的 push_front/push_back，覆盖更具体 |
| ghost ledger 与 tracked token 守恒 | [#632](https://github.com/asterinas/vostd/pull/632) | 漏检 | **命中** | 新版指出保留 token、清空 ledger、错误满足 clean_inv 的路径 |
| 私有辅助 proof 布局 | [#770](https://github.com/asterinas/vostd/pull/770) | 命中 | 命中 | 都识别辅助 lemma 打断 API；未观察到目标标签增益 |
| 同组 import 合并 | [#856](https://github.com/asterinas/vostd/pull/856) | 命中 | 命中 | 都保留 cfg 条件，未观察到目标标签增益 |
| 枚举契约冗余方向 | [#886](https://github.com/asterinas/vostd/pull/886) | 漏检 | 漏检 | 两版都把 match-enum-results 记为 compliance；新增文字未确保实际做逻辑检查 |
| 原始注释保留 | [#931](https://github.com/asterinas/vostd/pull/931) | 命中 | 命中 | 都识别原注释替换，没有把相邻未变的 resize/copy 误说成行为变化 |

上述文件范围另有一个 #770 的 `quantifiers-and-triggers` 标签，两版都未命中。若把该非直接目标对照也计入，范围内全部标签为 **原版 4/7，优化版 5/7**。这些分母不包含未审查文件，也不是整个 bench 的问题数。

匹配按根因而不是字面规则 ID 或完全相同行号：例如 #632 新版引用 `implement-inv-for-models`，标签是 `linear-resource-model-soundness`，但代码位置和绕过机制相同；#770 两版定位辅助块起点 :154，标签定位该块中的 bounds helper :244，按同类布局根因匹配。逐条依据见 [matches.json](matches.json)。

## 最值得向 reviewer 展示的例子

### #632：有具体新增发现

原版检查了 Inv 的存在和 borrowed-permission 契约，没有报告资源记账漏洞。优化版指出：

> a caller can mint an obligation, keep the tracked token, and reset frame_obligations to Multiset::empty()

源代码的 `inv()` 没有约束账本，而 `clean_inv()` 只增加空账本检查。新的 ghost 字段允许在 token 仍未清偿时制造“clean”的表象。该发现匹配 bench 标签，且没有声称已证明内存错误或 SMT 逻辑矛盾。

原始输出：[原版](raw/baseline/proof-engineering/pr-632-1be8099780ff.json)、[优化版](raw/candidate/proof-engineering/pr-632-1be8099780ff.json)。

### #886：应当保留的失败结果

原契约包含 `Some ⇒ 存在匹配` 和 `None ⇔ 无匹配`。由 Some 的逆否和 Option 穷尽性，`无匹配 ⇒ None` 已经成立；只需保留 `None ⇒ 无匹配`，同时保留 Some 的 payload 和 first-match 事实。

两版均未发现。不能把新版增加了相关提示当成已经解决了这个问题。后续可将该检查改成明确步骤：拆开等价式的两个方向，分别检查是否被其余子句蕴含，再检查删除某方向后的反例；这些建议尚未写入 PR，也没有用于重跑本实验。

原始输出：[原版](raw/baseline/maintainability/pr-886-fe5eb7f3e6aa.json)、[优化版](raw/candidate/maintainability/pr-886-fe5eb7f3e6aa.json)。更详细的推理见 [evidence-checks.md](evidence-checks.md)。

## 输出质量与额外发现

共保存 **71 条原始 Findings**，逐条进行静态核对，记录于 [adjudication.json](adjudication.json)。未匹配已知标签不直接算误报；没有用“报告总数更多”评价优化效果，也不在标签不完备时报告 precision/F1。

- 优化版 #770 的一条真实注释问题附带了过宽的 `Origin Rust` 标记建议；综合报告删除该附带建议，原始输出保留。
- ghost 模式变更、部分 single-use proof 内联、全局无调用方判断等缺乏工具链或完整依赖支持的建议标为 uncertain。
- 未修改的 specification persona 两次运行也有差异。例如原版报告了 #628 push_back 顺序问题，新版没有；新版在 #770 报告了私有 helper 的全局 CPU 数量前置条件限制。它们不应归因于 PR #933 的改动。
- 一些 raw Compliance 只是“现有证据没有支持一个 finding”，并非证明代码正确。#886 就展示了规则覆盖清单与真实检查效果的差别。
- 代理结束前自行完善行号和引文的中间版本保存在 [interim/](interim/README.md)，差异见 [interim-finalization.diff](interim-finalization.diff)。没有标签反馈、额外提示或重跑取优；评分使用最终 raw 输出。

## 对 PR 的建议

1. 将 #632 作为回答“为什么需要这些修改”的主要实验依据：仅看到 Inv 和 ghost 数据结构不够，需要追踪 token 与账本的关系，并寻找合法调用方的绕过路径。
2. 将命名、布局、import、注释修改描述为已有规范的执行澄清；本轮多数问题原版已经能发现，不声称这些项全部提高召回。
3. 明确承认枚举冗余检查本轮仍失败。后续改进后，用独立案例和重复运行验证，而不是用相同案例反复调提示后声称泛化提升。
4. alias/shadowing、恢复历史标记、求值顺序/panic、私有但关键 proof 等子情形尚未覆盖；本实验不能为它们提供有效性证明。

可直接编辑后使用的英文回复：[reviewer-response.md](reviewer-response.md)。未向 GitHub 发布。

## 结果文件与复核

| 文件 | 内容 |
|---|---|
| `skills/baseline/`、`skills/candidate/` | 完整原版/优化版 skill |
| `skill.diff`、`provenance/` | 原始差异、PR 元信息和 reviewer 评论快照 |
| `guidelines/`、`prompts/` | 共享规范和六份实际提示词 |
| `inputs/`、`context-snapshots.tar.gz` | 精确目标文件、diff 和完整无标签上下文副本 |
| `manifest.json`、`input-hashes.json` | 提交、目标范围和 3864 个输入文件的 SHA-256 |
| `raw/` | 两版各三个 persona 的 36 份最终原始输出及执行说明 |
| `reviews/` | 按案例综合的 12 份英文审查报告 |
| `gold.json`、`matches.json`、`metrics.json` | 评分标签、人工匹配与汇总 |
| `adjudication.json`、`validation.json` | 所有 Findings 的静态核对、schema/规则覆盖/输入哈希检查 |

`python3 experiments/pr-933-skill-ab/build_results.py` 可从持久化 raw、匹配和核对记录重新生成综合报告与计数，不调用模型。`collect.py` 从 manifest 指定的临时运行目录重新收集并校验结果；若该目录已删除，应使用归档恢复输入，而不是把重算报告误称为重新运行模型。提示词包含当时的绝对路径；移机重跑需要对应替换路径。底层模型版本和随机种子未通过本次代理接口导出，不能保证生成结果逐字复现。
