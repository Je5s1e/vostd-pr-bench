# 复现说明

[← 阅读入口](../README.md)

Python 3.9+，仅需标准库。以下命令在公开包根目录运行；脚本按自身位置解析数据路径，可在任意工作目录执行。

## 验证公开包

```sh
python3 scripts/validate.py
```

检查package manifest、179份公开review文本哈希、244标签与300原始意见计数、关联ID、CSV/JSON行数及阅读文档中的本地链接。只读，不更新任何归档文件。清单提供内容完整性检查，不是数字签名或判断正确性的证明。

## 确定性复算

```sh
python3 scripts/reproduce.py
```

在系统临时目录运行evaluate.py，依据冻结snapshot、RAW/NOTES中的基线判断和additional_judgments.txt中的新增判断，重生成JSON/CSV、规则表和逐条匹配表，与发布文件逐字节比较。完成后自动清理临时文件；不覆盖发布结果，也不访问原分析目录。

如需保留生成文件：

```sh
python3 scripts/evaluate.py --output build/results
```

输出目录不能位于发布的data/evidence/reports等内容目录内。脚本不产生新语义判定、不调用模型、不重跑review，也不重新生成报告的分析性文字。对判断的修改属于新的评估版本，需重新审阅报告与冻结manifest。

## 可选：核对外部原输入

```sh
python3 scripts/validate.py \
  --review-root /path/to/review-snapshots \
  --benchmark-root /path/to/vostd-pr-bench
```

两目录都应直接包含`pr-编号-SHA前缀`子目录；名称不必叫vostd-pr-test。该模式额外核对原review、diff、labels、metadata哈希，以及231个标签上下文文件的before/after内容。允许原始review或仅按本包规则规范化路径的review；其他文本变化视为漂移。

源码树不随本包分发；缺失文件会导致外部核对失败，不代表review意见被裁决为错误。此模式不启动编译、Verus、测试或远程下载。
