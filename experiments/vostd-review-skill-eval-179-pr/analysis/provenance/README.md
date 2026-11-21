# 来源、转换和完整性

[← 阅读入口](../README.md)

本公开副本整理自`analysis/review-eval-20261121`。原目录没有被修改；公开版仅重组文件、补充导航和数据说明、适配复算脚本，并规范化少量本机路径。没有调整标签匹配或得分。

| 文件 | 含义 |
|---|---|
| [source_manifest.json](source_manifest.json) | 被复制的原文件路径、SHA-256、目标路径及转换说明 |
| [export_changes.json](export_changes.json) | Scope路径规范化涉及的sample及前后review哈希 |
| [package_manifest.json](package_manifest.json) | 公开包文件列表及SHA-256；不含该清单本身 |
| [input_manifest.json](input_manifest.json) | 原179份review、diff、labels、metadata的输入指纹 |
| [context_integrity.json](context_integrity.json) | 原分析中231个标签上下文文件的一致性检查及哈希 |
| [validation.json](validation.json) | 原分析检查结果，时间字段属于原检查，并非公开包当前执行记录 |
| [input_exposure_audit.json](input_exposure_audit.json) | 16个残留历史evidence目录的文件清单；未观测实际访问行为 |

## 哈希的两个层次

179份全量冻结review中，3份Scope包含本机绝对工作区前缀，公开副本将其去掉，使路径从`vostd-pr-test/`开始。96份历史snapshot中有1份相同处理。只有Scope路径文本改变，finding及判断未变。

公开snapshot的`review_sha256`已重算；受影响项另存`original_review_sha256`。原输入manifest和原validation保留原始含义，不能直接用原输入哈希校验规范化后的公开文本。外部原输入核对使用原输入manifest，公开包校验使用package_manifest和公开snapshot文本哈希。

## 复现范围

公开包没有复制完整before/after源码树、diff或原历史evidence目录；这些文件仅记录来源及指纹。无需它们即可复算统计，不能据此重新执行review或复查全部源码。

本包保留96份历史档案以支持增量追溯；主要阅读入口不依赖它。历史脚本按原目录结构保存，不是推荐的公开复现入口。请使用[当前脚本](../scripts/README.md)。
