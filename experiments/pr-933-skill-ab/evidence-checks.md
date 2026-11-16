# 关键证据核对

这些是主代理在收到独立审查输出后的静态核对，不是向审查代理提供的提示，也不是 Verus 执行结果。

## #632：优化版新增命中的资源记账问题

文件：`ostd/specs/mm/frame/meta_region_owners.rs`。

- 原始 diff 将第 57 行的 `pub frame_obligations: Multiset<usize>` 改为 `pub ghost frame_obligations: Multiset<usize>`。
- `inv()`（64–86 行）约束 slot owners、地址和权限，但没有约束 obligation ledger。
- `clean_inv()`（254 行起）只检查 `inv()` 和 `frame_obligations.len() == 0`，其文档却把它解释为所有 obligation 都已清偿。
- `tracked_mint_frame_obligation`（278 行起）增加账本项并返回 tracked `DropObligation`。
- 因为账本字段是 public ghost，持有可变 owner 的调用方可以在保留 token 的同时将账本重置为空；其它字段不变，因而 `inv()` 不受影响，`clean_inv()` 可以再次成立。

这足以支持“clean-boundary 记账承诺可以被绕过”的静态问题。它不等同于证明 SMT 可推出 false，也不等同于构造了运行时 double-free。修复必须建立账本与 token 的守恒关系；只加一个无关 inv 或单纯把字段隐藏不能自动证明守恒。

原版 proof-engineering 输出把 Inv 的存在记为 compliance，并因 DropObligation 依赖源码缺失而没有提出这一问题。优化版 `632-proof-1` 则给出了字段重置、保留 token、clean_inv 错误成立的完整因果链。两个 specification 输出都没有报告该问题，因此此次新增命中来自被修改的 proof-engineering persona。

## #886：两版都漏掉的契约冗余

文件：`ostd/src/arch/x86/ex_table.rs:83–89`。令 E 表示存在匹配条目，N 表示返回 None。

- Some 分支承诺找到匹配条目以及正确 payload/首个匹配：`Some ⇒ E ∧ payload_facts`。
- None 子句写为 `N ⇔ ¬E`，等价于 `N ⇒ ¬E` 与 `¬E ⇒ N`。
- 由 Some 分支的逆否以及 Option 穷尽性，已有 `¬E ⇒ not Some ⇒ N`。
- 因此只需保留 `N ⇒ ¬E`，同时完整保留 Some 的 payload 和 first-match 事实。

不能删除整个 None 子句：仅有 Some 的条件保证时，即使存在匹配也允许返回 None。

两版 maintainability 都输出空 Findings。原版还明确把 None 等价式记为没有重复方向；优化版同样标记 compliance，引用位置却在第 21 行附近，未直接论证这个契约。因此“覆盖了规则清单”不能作为实际完成逻辑冗余检查的证据。本实验没有用这个说明指导重跑。

## #628：覆盖更具体，不能多算一个标签

原版在 `pop_front_embedded:382` 报告 tracked_ 命名问题，并泛指 wrapper/step 操作；优化版明确列出 `push_front_embedded:284`、`push_back_embedded:453` 和两个 pop helper。两个 push helper 通过 `&mut` 更新 tracked ownership，返回 unit。两版均命中同一个 bench 问题；新版的明确列举是输出覆盖的细化，不能算两个新增 true positives。

## #770、#856、#931：两版共有的命中

- #770：两版都引用第 154 行开始的私有辅助 lemma 区域并要求后置，措辞涵盖 bounds/capacity helpers；标签位于同一类辅助块中的 `lemma_cpucount_fits:244`。按共同根因匹配，接受为命中，并保留原始定位差异。
- #856：两版都合并无条件 arithmetic/prelude imports，并明确保留 cfg(irc11) Objective 的条件性。没有观察到这项新增指导带来的目标标签优势。
- #931：两版都识别第 121–122 行原注释被替换，要求保留原文，并没有把相邻未变的 resize/copy 误报为此次行为变化。

## 原始输出质量与修正

- 原版 maintainability 在尚未完成时曾将 DMA unused binder 锚定于 map:117；它在自身最后校验中独立改到了 daddr_inner:210，没有收到标签或主代理反馈。中间文件和 diff 保存在 interim/，最终评分使用 raw/；这不是额外重跑，也不应作为最终版本错误扣分。
- 优化版在 #770 的真实 rustdoc 修改问题中，附带要求为 new_empty 的 `let ret` 和擦除 proof scaffolding 增加原代码标记。该附带建议未建立独立的实际 executable rewrite 依据；综合报告保留注释问题，去掉这个过宽要求。
- 两版对 PhantomData-only 权限 marker 的 ghost 模式建议都未经过历史工具链验证，保留为 uncertain；不能把“try ghost struct”当作已确认可以编译的修复。
- 缺失依赖或工具链时，一些 raw Compliance 实际表达的是“未证实有问题”，并不构成“已证明符合规范”。综合结论不把这些记录当成正确性证书。
