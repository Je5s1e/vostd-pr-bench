# VOSTD Review Skill Evaluation — 179 Snapshots

`vostd-code-review` 在 **fast 静态审查配置**下，对 **179 个快照（164 个独立 PR）**的评估汇报。结果冻结于 2026-11-21。本目录包含阅读版报告、逐条标签匹配、统计数据和离线复现工具，可以独立复制到公开仓库中。

这是一份描述性评估：**不是严格隔离的封存测试，也不是完整 skill 流程或演化收益的对照实验。** 新增匹配由单一 agent 判断，前96份判断沿用，未经过独立人工校准。未匹配意见不等于误报。

## 从这里开始

| 你想了解什么 | 推荐入口 |
|---|---|
| 两分钟看懂范围、结果和改进重点 | [省流版总结](reports/quick-summary.md) |
| 先看结论和下一步 | [总结与改进建议](reports/summary.md) |
| 查看完整结果、案例和限制 | [完整分析报告](reports/analysis.md) |
| 理解如何判定命中、分母是什么 | [评测协议](methodology/protocol.md) |
| 核查某个 PR 的标签匹配 | [快照索引](reports/sample-index.md) → [逐条匹配表](reports/label-matches.md) |
| 下载数据自行统计 | [数据字典与文件导航](methodology/data-dictionary.md) |
| 验证文件或复算指标 | [复现说明](scripts/README.md) |
| 查来源、哈希和公开副本改动 | [来源与完整性](provenance/README.md) |

## 关键结果

| 指标 | 结果 |
|---|---:|
| 完成的审查快照 / 独立 PR | 179 / 164 |
| 基准标签 | 244 |
| 完整命中（严格召回） | **58/244 = 23.8%** |
| 完整＋部分命中（宽松召回） | 65/244 = 26.6% |
| semantic / guideline 严格召回 | 47/133 = 35.3% / 11/111 = 9.9% |
| 排除3个已在after修复的标签后，严格召回 | 58/241 = 24.1% |
| 原始报告意见 | 300 |
| 完整关联 / 仅部分关联 / 未关联标签的意见 | 56 / 7 / 237 |

主要改进方向是具体规则覆盖、跨API资源与身份关系、输入输出契约可用性，以及声明和调用的一致性。237条未关联意见尚未完整裁决，因此不报告precision、误报率或F1。当前工作区还发现16个样本残留历史evidence，无法确认review时是否读取；详见[限制与隔离审计](methodology/protocol.md)。

## 目录结构

```text
.
├── README.md                 # 阅读入口和关键结果
├── SOURCES.md                # 数据、skill来源与许可状态
├── reports/                  # 总结、完整报告、逐条匹配
├── methodology/              # 评测协议、数据字典
├── data/                     # 全量统计及JSON/CSV明细
├── evidence/                 # 冻结报告/标签、skill归档、新增匹配判断
├── provenance/               # 输入指纹、原检查记录、公开副本转换记录
├── scripts/                  # 离线复算和完整性检查
└── archive/baseline-96/       # 早期96份中间结果，仅供追溯
```

当前结论以 `reports/` 与 `data/` 为准，`archive/` 不是另一组独立对照实验。公开副本的整理没有修改原 `analysis/review-eval-20261121`，也没有重新审查PR或修改skill。

## 离线复现

需要 Python 3.9+，仅使用标准库。在本目录运行：

```sh
python3 scripts/validate.py
python3 scripts/reproduce.py
```

不需要模型调用、API密钥、网络或原始工作区。第一条验证公开包；第二条依据冻结判断重新计算并比较发布结果。**复算计数不等于重新验证判断正确性。** 如需检查源码/diff或重新执行review，需另行取得原始输入和运行环境。

本机绝对路径只在公开副本中改为仓库相对路径，受影响review同时保存原始哈希和公开文本哈希。详情见[转换记录](provenance/export_changes.json)。
