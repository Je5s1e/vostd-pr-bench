# 数据格式与导出要求

## 固定提交与源码

`after` 为所选审查提交，`before` 为该提交相对于目标分支的比较基线。优先使用可证实的历史 base；否则取选定审查时刻之前目标分支的 first-parent tip，与 head 求 merge-base。记录历史 tip SHA、时间依据和计算方法；不要使用当前目标分支的 tip 代替历史基线，不能推断可靠基线则暂缓。

从固定 Git 对象生成完整 diff，例如 `git diff --binary --full-index --no-ext-diff --no-textconv <base> <head> --`，以原始字节保存为 `diff.patch` 并计算 SHA-256。不要使用会随 PR 更新的当前 GitHub diff 代替历史 diff。变更路径取同一次比较，重命名时保留两侧路径，可使用 `git diff --name-only --no-renames -z <base> <head> --` 获取并集。

每侧导出该提交完整 `ostd/`、diff 涉及的 `ostd/` 外文件和上游根目录版权/许可文件；保留实际存在的文件、路径、可执行位及符号链接，不复制 `.git` 或构建缓存。不沿符号链接读取工作区外数据。新增文件只在 after，删除文件只在 before。

被修改的 gitlink 子模块按各侧固定 SHA 展开，保留子模块许可，记录 SHA 与 included=true；未涉及修改的子模块记录 SHA 与 included=false，不把子模块 SHA 当普通文件写入。需要的嵌套子模块按相同原则处理。文件数量按实际导出普通文件和符号链接计数。

## metadata.json

保持现有字段的含义和类型；新案例使用以下值：

- `schema_version`: 1；`dataset_version`: 2（现有数据格式版本，不表示属于原冻结批次）。
- `sample_id`: 与目录名一致；`pr_number`: 整数。
- `title`, `url`, `repository`: 官方 PR 的真实数据；repository 固定 `https://github.com/asterinas/vostd`。
- `title_source`: `github_pr_metadata_at_collection`。
- `base_sha`, `head_sha`: 完整 40 位提交 SHA。
- `base_method`: 写明真实构造方法及所用历史 tip，不能复制其他案例的描述冒充已执行步骤。
- `original_split`: `incremental`，不得自动分配为 `dev` 或 `heldout`。
- `source_scope`: `Complete ostd/ at each commit, changed files outside ostd/, and original license/notice files. Changed submodules are expanded at their pinned commits.`
- `changed_paths`: 相对仓库根目录的变更路径数组。
- `diff_sha256`: diff 原始字节的 SHA-256。
- `versions.before` / `versions.after`: 含 `commit`, `file_count`, `submodules`（每项含 `path`, `sha`, `included`）及 `license_files`。
- `known_issue_count`: issues 数组长度。
- 新增 `collection`: 含 `collected_at`（UTC ISO 8601）、`reviewed_at`、`upstream_updated_at`、`source_urls` 和 `guideline_sources`（适用时包含规范 `commit`, `path`, `url`）。用于区分增量来源与原冻结数据。

## labels.json

顶层保留 `schema_version: 1`, `sample_id`, `issues`，新案例的 `status` 使用 `incremental_source_adjudicated`。不要沿用 `frozen_source_adjudicated`。

每条 issue 保留现有字段：

- `id`: `<sample_id>:<来源类型>-<原始ID>`，来源类型用 `review-comment`、`issue-comment` 或 `review`，避免不同 API 的数字 ID 冲突。
- `original_label_id`: `null`（新采集没有旧冻结标签 ID）。
- `category`: `guideline` 或 `semantic`。
- `description`: 简洁、可独立理解的问题陈述，建议与现有标签一致使用英文；不直接复制整段讨论。
- `locations`: 非空数组；每项包含 `version`（before/after）、`path`、从 1 开始且两端包含的 `start_line` / `end_line`。行号从导出文件重新定位，不机械复制 GitHub 的旧行号或 diff position。
- `rationale`: 为什么该固定版本存在该问题，包括适用规则或语义失败条件。
- `source_evidence`: 真实源码摘录，标明路径、版本和行号。
- `rule_ids`: 实际核实的规则标识，无适用条目时为空数组，不编造规则 ID。
- `review_url`: 主要来源的永久评论或 review 链接。
- `related_comment_ids`: 原始 ID 字符串数组；同时新增 `sources` 数组，每项含 `kind`, `id`, `url`, `commit_id`（没有则 null），以区分来源类型。
- `verification`: 实际执行的验证及限制。

校验脚本只检查结构和文件一致性。agent 仍需核对问题成立、规范依据、快照与 Git 对象一致以及证据真实；结构通过不等于标签正确。
