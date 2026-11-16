# 优化点与案例对应关系

本表是选样依据，不提供给审查代理。所有案例均来自已有 bench；没有为优化版另造更容易命中的代码。

| PR #933 的变化 | 对应 bench PR | 对照关注点 | 未覆盖部分 |
|---|---|---|---|
| 检查被删改的原始注释；区分注释与行为变化 | [#931](https://github.com/asterinas/vostd/pull/931) | `to_flat_binary` 的原注释被替换，但相邻 resize/copy 逻辑没有改变；不能把原文保留要求误讲成运行时 bug | 历史标记恢复、求值顺序和 panic diagnostics |
| 按规范定义的组分别合并 import；检查作用域 | [#856](https://github.com/asterinas/vostd/pull/856) | 同组的两条无条件 vstd 导入可合并；`cfg(irc11)` 条件不能丢失 | alias、shadowing 和跨原始 exec import 分组的反例 |
| 通过枚举穷尽性识别冗余方向，保留独立保证 | [#886](https://github.com/asterinas/vostd/pull/886) | `None <==> no_match` 的反向已由 Some 契约隐含；前向仍必需 | Result/Err payload 的独立保证反例 |
| 所有权 proof helper 命名包括无返回值 helper | [#628](https://github.com/asterinas/vostd/pull/628) | 资源转移 helper 应用 tracked_，不是 lemma_；额外记录 push helper 的覆盖情况 | 仅有 tracked 参数的 exec API 不应改名的反例 |
| 辅助 lemma 与 API/critical proof 区分 | [#770](https://github.com/asterinas/vostd/pull/770) | 私有 bounds-fitting / representation helper 不能打断 API 区域 | 私有但关键的 proof 必须留在前面的反例 |
| 追踪 token 与 ghost ledger，构造可行的清账绕过 | [#632](https://github.com/asterinas/vostd/pull/632) | public ghost 字段可被改写；clean_inv 的空账本检查不能建立线性 token 已清偿的承诺 | 私有 ledger 的合法 mutation path；更复杂 transfer/redemption 协议 |

这些约束大多已经存在于共享 coding guidelines 中；原版 persona 本身也要求逐项检查完整规范。因而本实验关注的是显式检查步骤对执行效果的影响，不能仅凭“新版提示写得更详细”推定召回率会提高。
