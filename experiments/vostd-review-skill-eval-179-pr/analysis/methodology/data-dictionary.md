# 数据字典

[← 阅读入口](../README.md)

## 选择文件

| 文件 | 单位 / 行数 | 用途 |
|---|---|---|
| [metrics.json](../data/metrics.json) | 一份全量汇总 | 总体、批次、类别、机制、规则及敏感性统计 |
| [cases.csv](../data/cases.csv) / [JSON](../data/cases.json) | 179个快照 | 查看每份报告的标签数、意见数和命中数 |
| [label_matches.csv](../data/label_matches.csv) / [JSON](../data/label_matches.json) | 244个标签 | 根因判断、理由、位置和关联finding |
| [findings.csv](../data/findings.csv) / [JSON](../data/findings.json) | 300个原始报告项 | 原文、严重度和标签关联 |
| [rule_metrics.csv](../data/rule_metrics.csv) | 一个rule_id一行 | 按标签规则统计，非互斥 |
| [snapshot.json](../evidence/snapshot.json) | 179份冻结输入记录 | review全文、参照标签和benchmark metadata |
| [skill_sources.json](../evidence/skill_sources.json) | 归档skill文件 | 检查被分析的skill及persona说明 |
| [additional_judgments.txt](../evidence/additional_judgments.txt) | 127条新增判断 | 剩余83快照的判断输入；基线判断保留在脚本RAW/NOTES中 |

CSV使用UTF-8 BOM，便于表格软件读取；JSON为UTF-8。CSV中的list/dict字段使用JSON字符串序列化，导入后需解析。JSON中的数组与对象保留结构。

## 公共键与编号

- `sample`：`pr-<PR编号>-<head SHA前缀>`，是快照键；不是独立PR键。
- `pr_number`：PR编号；多个sample可共享它。
- `label_id`：标签唯一ID；`label_index`在该快照内从0开始。
- `finding` / `finding_ids`：该快照原始报告项编号，从1开始，保持High/Medium/Low中的原顺序；不是模型提供的稳定ID。
- 关联finding必须使用组合键 **(sample, finding)**，不能只凭finding数字连接。
- `batch`：`baseline_96`或`remaining_83`，仅表示分析处理批次。

## cases

`labels`为标签数；`findings`为原始报告项数；`full`、`partial`为完整和部分命中的标签数；`excluded`为X数量，并不表示已经从原分母剔除。`strict_recall = full / labels`。M可由`labels-full-partial-excluded`得到。

## label_matches

`category`为`semantic`或`guideline`。`group` / `group_name`是分析用机制分类。`status`取F/P/M/X，解释见[协议](protocol.md)。`finding_ids`及`finding_titles`记录命中依据；M/X通常为空。`description`、`rule_ids`、`locations`来自标签；位置包含before/after、路径及行号。`reason`为匹配判断理由，`judgment_source`与`evaluator_version`记录评估来源和版本。

机制编码：T显式证明缺口；O所有权/身份/资源；I模型/状态机；C契约/泛型/边界；B构建/工具链；R运行时/生命周期；G规范复用/放置/helper；H命名/模式/风格；E执行代码保存；W文档。分类不等于缺陷真伪。

## findings

`severity`来自原报告；`title`和`text`保留意见内容。`full_label_ids`、`partial_label_ids`为关联标签。`benchmark_status`取：

- `full_match`：完整关联至少一个标签。
- `partial_match`：没有完整关联，但有部分关联。
- `unmatched_not_adjudicated_false`：未关联，**未被裁决为false positive**。

`reported_rule_ids`按原文出现的规则ID提取，不推断未写明的规则，不表示实际执行率。原始报告项可能复合；不能当作已原子化去重的问题。

## metrics及来源哈希

`issue_stats`与各分组中的`n/full/partial/miss/fixed_in_after`是标签计数；`strict_recall/lenient_recall`为0到1的比例。`by_rule`可重复计数，`by_group`互斥。`finding_rule_mentions`同样非互斥。`not_measured`中`null`表示未测，不能当零。

公开snapshot中，`review_sha256`对应本包review文本；若规范化过本机路径，额外的`original_review_sha256`对应原始文件。`provenance/input_manifest.json`保存原输入哈希，`package_manifest.json`保存本包文件哈希，两者用途不同。

冻结snapshot含评估器专用标签、历史信息及skill全文，**不能直接拿来作为无标签Reviewer输入**。
