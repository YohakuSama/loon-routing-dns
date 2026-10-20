# 来源更新与候选差异审核（只读）

RC2 当前来源基准为 `rules/snapshots/phase03/generated/` 的不可变合并快照；其原始上游行级血统 **NOT_RECOVERABLE_FROM_MERGED_SNAPSHOT**，此工具不能假定每条规则来自哪一家仓库。

## 预审单个来源文件

```bash
python3 scripts/phase07_source_update_review.py \
  --source rules/snapshots/phase03/generated/Google.list \
  --proposed /tmp/Google.proposed.list \
  --report /tmp/google-update-review.json
```

输出固定的 SHA256、新旧规则计数、按 matcher 类型分组的新增/删除计数与最多 30 行样例。输出标为 `PENDING_REVIEW_NOT_PUBLISHED`，不会修改任何正式规则、冻结来源或订阅。

确认合法授权与归属、可用来源 Commit、回归结果后，维护者可在 **新的 PR** 中物化新不可变快照，逐项更新 `engine_manifest.json` 与 `sources.lock.json` 的哈希、Git blob 以及来源描述。必须运行阶段 02/04/05/06/07 全套离线审计并生成新的候选差异报告；发布版本不得复用已经冻结的 `vNext-RC2` 目录或改写旧候选 SHA。受影响的真机验证须重新执行。

新来源绝对不能从 `rules/generated/` 或 `rules/releases/` 生产输出中提取，不能直接从 `main` 或任何上游动态 URL 无审核同步到现役配置。CI 对新 PR **只读**，若许可未核实或测试证据未齐全即阻止正式发布。
